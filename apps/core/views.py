import hashlib
import hmac
import json
import os
from uuid import UUID
from django.utils import timezone
import jwt
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .token import JWTAuthentication
from ..users.serializers import UserSerializer
from ..users.models import User
from datetime import datetime, timedelta
from ..products.models import Product
from ..products.serializers import ProductSerializer
from .models import Transaction
from .serializers import TransactionSerializer

# Create your views here.

class IndexViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return render(request, "index.html", context={"products": serializer.data})

    @action(methods=["post"], detail=False, url_path="paystack-webhook")
    def paystack_webhook(self, request):
        request_body = request.body
        token = os.getenv('PAYSTACK_API_TOKEN').encode("utf-8")
        generated_hash = hmac.new(token, request_body, hashlib.sha512).hexdigest()
        signature = request.headers.get("x-paystack-signature")

        if generated_hash != signature:
            return Response({"detail": "Invalid signature"}, status=403)

        event = json.loads(request_body.decode("utf-8"))
        #  Sample output.
        """ 
        Received Paystack event: {
            'event': 'charge.success', 'data': {
                'id': 5224206525, 'domain': 'test', 'status': 'success', 'reference': '1e5cfd98-2bd8-4207-96f4-05c89efce3cf', 
                'amount': 16500000, 'message': None, 'gateway_response': 'Approved', 'paid_at': '2025-08-09T20:51:04.000Z', 
                'created_at': '2025-08-09T20:50:54.000Z', 'channel': 'mobile_money', 'currency': 'KES', 'ip_address': '41.90.182.57', 
                'metadata': {
                    'product_id': '02917bed-d42e-446a-bf71-ca0834619d92', 'user_id': '5', 'sale_id': '6351dedd-0512-4dc0-9251-4e0fabe034da','order_number': 'KY4DP41JUN'
                }, 
                'fees_breakdown': None, 'log': None, 'fees': 247500, 'fees_split': None, 
                'authorization': {
                    'authorization_code': 'AUTH_rxeqfxdack', 'bin': '071XXX', 'last4': 'X000', 'exp_month': '12', 'exp_year': '9999', 'channel': 'mobile_money', 'card_type': '', 
                    'bank': 'Airtel Kenya', 'country_code': 'KE', 'brand': 'Airtel kenya', 'reusable': False, 'signature': None, 'account_name': None, 
                    'receiver_bank_account_number': None, 'receiver_bank': None
                }, 
                'customer': {
                    'id': 297846932, 'first_name': None, 'last_name': None, 'email': 'doejane@example.com', 'customer_code': 'CUS_6eib935oqc94h9n', 'phone': None, 
                    'metadata': None, 'risk_action': 'default', 'international_format_phone': None
                }, 
                'plan': {}, 'subaccount': {}, 'split': {}, 'order_id': None, 'paidAt': '2025-08-09T20:51:04.000Z', 'requested_amount': 16500000, 'pos_transaction_data': None, 
                'source': {
                    'type': 'api', 'source': 'merchant_api', 'entry_point': 'transaction_initialize', 'identifier': None
                }
            }
        }
        """

        tx_data = event["data"]

        transaction_payload = {
            "id": UUID(tx_data["metadata"]["sale_id"]),
            "status": tx_data["status"],
            "paystack_id": tx_data["id"],
            "reference": tx_data["reference"],
            "amount": tx_data["amount"] / 100,
            "currency": tx_data["currency"],
            "gateway_response": tx_data["gateway_response"],
            "paid_at": tx_data["paid_at"],
            "created_at": tx_data["created_at"],
            "channel": tx_data["channel"],
            "ip_address": tx_data.get("ip_address"),
            "product_id": UUID(tx_data["metadata"]["product_id"]),
            "user_id": int(tx_data["metadata"]["user_id"]),
            "order_number": tx_data["metadata"]["order_number"],
            "fees": tx_data["fees"],
            "card_type": tx_data["authorization"]["card_type"],
            "last4": tx_data["authorization"]["last4"],
            "bank": tx_data["authorization"]["bank"],
            "customer_email": tx_data["customer"]["email"],
            "customer_code": tx_data["customer"]["customer_code"],
        }

        if not Transaction.objects.filter(pk=transaction_payload["id"]).exists():
            serializer = TransactionSerializer(data=transaction_payload)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return Response(status=200)

    @action(methods=["get"], detail=False)
    def transactions(self, request, *args, **kwargs):
        obj = Transaction.objects.all()
        serializer = TransactionSerializer(obj, many=True)
        return Response(serializer.data)

class AuthViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_authenticators(self):
        if self.request.method == "GET":
            return [JWTAuthentication()]
        return []

    def get_permissions(self):
        if self.request.method == "GET":
            return [IsAuthenticated()]
        return []

    def list(self, request, *args, **kwargs):
        return Response({"data": self.get_serializer(request.user).data}, status=200)

    def create(self, request, *args, **kwargs):
        data = JSONParser().parse(request)
        email = data['email']
        password = data['password']

        try:
            user = get_object_or_404(User, email=email)
        except:
            return Response(status=404)

        if not user.check_password(password):
            return Response(status=400)

        payload = {"id": str(user.id), "exp": datetime.utcnow() + timedelta(hours=1)}

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        user.last_login = timezone.now()
        user.save()

        return Response({"token": token}, status=200)
