from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Seller(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credit = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(Decimal('0.00'))])

    def __str__(self):
        return f"{self.user.username} - Credit: {self.credit}"

    @classmethod
    def get_seller_for_update(cls, seller_id):
        return cls.objects.select_for_update().get(id=seller_id)

class PhoneNumber(models.Model):
    number = models.CharField(max_length=15, unique=True)

    def __str__(self):
        return self.number

class Transaction(models.Model):
    transaction_id = models.CharField(max_length=255, unique=True)
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='%(class)ss')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['seller', 'timestamp']),
        ]

    @classmethod
    def generate_transaction_id(cls, seller_id, amount):
        return f"{cls.__name__.upper()}_{seller_id}_{amount}_{timezone.now().timestamp()}"

    @classmethod
    def transaction_exists(cls, transaction_id):
        return cls.objects.filter(transaction_id=transaction_id).exists()

class CreditTransaction(Transaction):
    TRANSACTION_TYPES = [
        ('INCREASE', 'Increase'),
        ('DECREASE', 'Decrease'),
    ]
    transaction_type = models.CharField(max_length=8, choices=TRANSACTION_TYPES)

    def __str__(self):
        return f"{self.seller.user.username} - {self.transaction_type} - {self.amount}"

class ChargeTransaction(Transaction):
    phone_number = models.ForeignKey(PhoneNumber, on_delete=models.CASCADE)

    class Meta(Transaction.Meta):
        indexes = Transaction.Meta.indexes + [
            models.Index(fields=['phone_number', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.seller.user.username} - {self.phone_number.number} - {self.amount}"