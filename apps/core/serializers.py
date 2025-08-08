from rest_framework.serializers import ModelSerializer
from .models import Transaction

class TransactionSerializer(ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"