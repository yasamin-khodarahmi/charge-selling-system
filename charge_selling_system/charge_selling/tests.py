from django.test import TransactionTestCase
from django.contrib.auth.models import User
from decimal import Decimal
from charge_selling.models import Seller, PhoneNumber, ChargeTransaction, CreditTransaction
from django.db import transaction, connections
from django.core.exceptions import ValidationError
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.db import connection
import uuid
import time
from django.utils import timezone

class ParallelAccountingSystemTest(TransactionTestCase):
    databases = ['default']

    @classmethod
    def setUpClass(cls):
        cls.unique_db_name = f"test_b2b_charge_selling_{uuid.uuid4().hex[:10]}"
        cls.databases = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': cls.unique_db_name,
                'USER': 'postgres',
                'PASSWORD': 'mypassword',
                'HOST': 'localhost',
                'PORT': '5432',
            }
        }
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        connections['default'].close()
        with connections['default'].cursor() as cursor:
            # Terminate all other connections
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{cls.unique_db_name}'
                AND pid <> pg_backend_pid();
            """)
            time.sleep(2)
            # drop the database
            cursor.execute(f"DROP DATABASE IF EXISTS {cls.unique_db_name}")
        
        super().tearDownClass()

    def setUp(self):
        self.num_sellers = 2
        self.num_phone_numbers = 10
        self.num_credit_increases = 10
        self.num_charge_sales = 1000
        self.max_workers = 20

        self.sellers = []
        for i in range(self.num_sellers):
            user = User.objects.create_user(username=f'seller{i}', password=f'password{i}')
            seller = Seller.objects.create(user=user, credit=Decimal('0'))
            self.sellers.append(seller)

        self.phone_numbers = [
            PhoneNumber.objects.create(number=f'0{random.randint(100000000, 999999999)}')
            for _ in range(self.num_phone_numbers)
        ]

    def increase_credit(self, seller):
        amount = Decimal(random.randint(10000, 100000))
        transaction_id = f"CREDIT_INCREASE_{seller.id}_{amount}_{timezone.now().timestamp()}"
        try:
            with transaction.atomic():
                seller = Seller.objects.select_for_update().get(id=seller.id)
                if CreditTransaction.objects.filter(transaction_id=transaction_id).exists():
                    return Decimal('0')
                seller.credit += amount
                seller.save()
                CreditTransaction.objects.create(
                    seller=seller,
                    amount=amount,
                    transaction_type='INCREASE',
                    transaction_id=transaction_id
                )
            return amount
        except Exception as e:
            print(f"Error in credit increase: {str(e)}")
            return Decimal('0')

    def perform_charge_sale(self):
        seller = random.choice(self.sellers)
        charge_amount = Decimal(random.randint(1000, 5000))
        phone_number = random.choice(self.phone_numbers)
        transaction_id = f"CHARGE_SALE_{seller.id}_{phone_number.number}_{charge_amount}_{timezone.now().timestamp()}"
        try:
            with transaction.atomic():
                seller = Seller.objects.select_for_update().get(id=seller.id)
                if ChargeTransaction.objects.filter(transaction_id=transaction_id).exists():
                    return False
                if seller.credit >= charge_amount:
                    seller.credit -= charge_amount
                    seller.save()
                    ChargeTransaction.objects.create(
                        seller=seller,
                        phone_number=phone_number,
                        amount=charge_amount,
                        transaction_id=transaction_id
                    )
                    return True
                else:
                    return False
        except Exception as e:
            print(f"Error in charge sale: {str(e)}")
            return False

    def test_parallel_accounting_system(self):
        # Perform credit increases
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            credit_futures = [executor.submit(self.increase_credit, seller) 
                              for seller in self.sellers 
                              for _ in range(self.num_credit_increases)]
            
            for future in as_completed(credit_futures):
                future.result()

        successful_sales = 0
        failed_sales = 0

        # Perform parallel charge sales
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.perform_charge_sale) for _ in range(self.num_charge_sales)]
            
            for future in as_completed(futures):
                if future.result():
                    successful_sales += 1
                else:
                    failed_sales += 1

        # Verify results
        for seller in self.sellers:
            seller.refresh_from_db()
            expected_credit = sum(t.amount for t in CreditTransaction.objects.filter(seller=seller, transaction_type='INCREASE')) - \
                              sum(t.amount for t in ChargeTransaction.objects.filter(seller=seller))
            
            self.assertEqual(seller.credit, expected_credit,
                             f"Seller {seller.user.username} credit mismatch. Expected {expected_credit}, got {seller.credit}")
            
            self.assertGreaterEqual(seller.credit, 0, f"Seller {seller.user.username} has negative credit: {seller.credit}")

        total_transactions = ChargeTransaction.objects.count()
        self.assertEqual(total_transactions, successful_sales,
                         f"Number of successful sales ({successful_sales}) does not match total transactions in database ({total_transactions})")

        # Check for duplicate transactions
        credit_transaction_ids = CreditTransaction.objects.values_list('transaction_id', flat=True)
        self.assertEqual(len(credit_transaction_ids), len(set(credit_transaction_ids)), 
                         "Duplicate credit transactions detected")

        charge_transaction_ids = ChargeTransaction.objects.values_list('transaction_id', flat=True)
        self.assertEqual(len(charge_transaction_ids), len(set(charge_transaction_ids)), 
                         "Duplicate charge transactions detected")

        print(f"Test completed using database: {self.unique_db_name}")
        print(f"Test completed with {self.num_sellers} sellers, {self.num_phone_numbers} phone numbers, "
              f"{self.num_credit_increases} credit increases per seller, {successful_sales} successful sales, "
              f"and {failed_sales} failed sales.")

        # Check query count for performance
        print(f"Total queries executed: {len(connection.queries)}")

        for conn in connections.all():
            conn.close()

if __name__ == '__main__':
    import unittest
    unittest.main()