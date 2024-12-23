from rest_framework import serializers
from .models import Seller, PhoneNumber, CreditTransaction, ChargeTransaction

class SellerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seller
        fields = ['id', 'user', 'credit']

class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ['id', 'number']

class CreditTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditTransaction
        fields = ['id', 'seller', 'amount', 'transaction_type', 'timestamp']

class ChargeTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChargeTransaction
        fields = ['id', 'seller', 'phone_number', 'amount', 'timestamp']

class CreditIncreaseRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)

class ChargeSaleSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0.01)