from django.shortcuts import render, get_object_or_404, redirect
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .models import Product
from .serializers import ProductSerializer
from uuid import uuid4, UUID
from ..core.paystack import checkout, confirmation
from ..core.services import generate_order_number
from ..core.serializers import TransactionSerializer
from ..core.models import Transaction

# Create your views here.

class ProductsViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        product = get_object_or_404(Product, pk=pk)
        return render(request, "product_details.html", {"product": product, "purchase_link": f"{request.scheme}://{request.get_host()}/products/{pk}/purchase/"})

    @action(detail=True, methods=["get"])
    def purchased(self, request, pk=None):
        product_id = pk
        product = Product.objects.get(pk=product_id)

        reference = request.GET.get("reference")

        verify = confirmation(reference)

        if verify.get("status") and verify["data"]["status"] == "success":
            tx_data = verify["data"]

            transaction_payload = {
                "id": UUID(tx_data["metadata"]["sale_id"]),
                "status": tx_data["status"],
                "paystack_id": tx_data["id"],
                "reference": tx_data["reference"],
                "amount": tx_data["amount"],
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

            return render(request, "purchased.html", {"product": product, "transaction": tx_data})

        return render(request, "failed.html", {"product": product})

    @action(detail=True, methods=["post"])
    def purchase(self, request, pk=None):
        product_id = pk

        product = Product.objects.get(pk=product_id)

        payload = {
            "email": "doejane@example.com",
            "amount": int(product.price) * 100,
            "currency": "KES",
            "channels": ["card", "bank_transfer", "bank", "ussd", "qr", "mobile_money"],
            "reference": str(uuid4()),
            "callback_url": f"{request.scheme}://{request.get_host()}/products/{product_id}/purchased/",
            "metadata": {
                "product_id": product_id,
                "user_id": 5,
                "sale_id": str(uuid4()),
                "order_number": generate_order_number()
            },
            "label": f"Checkout for {product.name}"
        }

        status, response_data = checkout(payload)
        if status:
            return redirect(response_data)

        return Response({
            "message": response_data, "status":status
        })
