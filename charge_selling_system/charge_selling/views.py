from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Seller, PhoneNumber, CreditTransaction, ChargeTransaction
from .serializers import (
    SellerSerializer, PhoneNumberSerializer, CreditTransactionSerializer,
    ChargeTransactionSerializer, CreditIncreaseRequestSerializer, ChargeSaleSerializer
)
import logging
from django.db.models import F

logger = logging.getLogger(__name__)

class SellerViewSet(viewsets.ModelViewSet):
    queryset = Seller.objects.all()
    serializer_class = SellerSerializer

    @action(detail=True, methods=['post'])
    def increase_credit(self, request, pk=None):
        seller = self.get_object()
        serializer = CreditIncreaseRequestSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            try:
                with transaction.atomic():
                    seller = Seller.get_seller_for_update(seller.id)
                    transaction_id = CreditTransaction.generate_transaction_id(seller.id, amount)
                    
                    if CreditTransaction.transaction_exists(transaction_id):
                        raise ValidationError("This credit increase has already been processed.")
                    
                    seller.credit = F('credit') + amount
                    seller.save()
                    
                    CreditTransaction.objects.create(
                        seller=seller,
                        amount=amount,
                        transaction_type='INCREASE',
                        transaction_id=transaction_id
                    )
                
                seller.refresh_from_db()
                return Response({'status': 'credit increased', 'new_credit': seller.credit})
            except ValidationError as e:
                logger.error(f"Validation error in increase_credit for seller {seller.id}: {str(e)}")
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected error in increase_credit for seller {seller.id}: {str(e)}")
                return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def sell_charge(self, request, pk=None):
        seller = self.get_object()
        serializer = ChargeSaleSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data['phone_number']
            amount = serializer.validated_data['amount']
            try:
                with transaction.atomic():
                    seller = Seller.get_seller_for_update(seller.id)
                    transaction_id = ChargeTransaction.generate_transaction_id(seller.id, amount)
                    
                    if ChargeTransaction.transaction_exists(transaction_id):
                        raise ValidationError("This charge sale has already been processed.")
                    
                    if seller.credit < amount:
                        raise ValidationError("Insufficient credit")
                    
                    seller.credit = F('credit') - amount
                    seller.save()
                    
                    phone_obj, _ = PhoneNumber.objects.get_or_create(number=phone_number)
                    ChargeTransaction.objects.create(
                        seller=seller,
                        phone_number=phone_obj,
                        amount=amount,
                        transaction_id=transaction_id
                    )
                
                seller.refresh_from_db()
                return Response({'status': 'charge sold successfully', 'remaining_credit': seller.credit})
            except ValidationError as e:
                logger.error(f"Validation error in sell_charge for seller {seller.id}: {str(e)}")
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected error in sell_charge for seller {seller.id}: {str(e)}")
                return Response({'error': 'An unexpected error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def get_credit(self, request, pk=None):
        seller = self.get_object()
        return Response({'credit': seller.credit})

    @action(detail=True, methods=['get'])
    def get_transactions(self, request, pk=None):
        seller = self.get_object()
        transactions = CreditTransaction.objects.filter(seller=seller).order_by('-timestamp')[:100]
        serializer = CreditTransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def get_charge_sales(self, request, pk=None):
        seller = self.get_object()
        charge_sales = ChargeTransaction.objects.filter(seller=seller).order_by('-timestamp')[:100]
        serializer = ChargeTransactionSerializer(charge_sales, many=True)
        return Response(serializer.data)

class PhoneNumberViewSet(viewsets.ModelViewSet):
    queryset = PhoneNumber.objects.all()
    serializer_class = PhoneNumberSerializer

class CreditTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CreditTransaction.objects.all()
    serializer_class = CreditTransactionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        seller_id = self.request.query_params.get('seller_id')
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)
        return queryset.order_by('-timestamp')[:1000]

class ChargeTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChargeTransaction.objects.all()
    serializer_class = ChargeTransactionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        seller_id = self.request.query_params.get('seller_id')
        phone_number = self.request.query_params.get('phone_number')
        if seller_id:
            queryset = queryset.filter(seller_id=seller_id)
        if phone_number:
            queryset = queryset.filter(phone_number__number=phone_number)
        return queryset.order_by('-timestamp')[:1000]