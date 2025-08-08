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
