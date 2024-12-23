from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SellerViewSet, PhoneNumberViewSet, CreditTransactionViewSet, ChargeTransactionViewSet

router = DefaultRouter()
router.register(r'sellers', SellerViewSet)
router.register(r'phone-numbers', PhoneNumberViewSet)
router.register(r'credit-transactions', CreditTransactionViewSet)
router.register(r'charge-transactions', ChargeTransactionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
