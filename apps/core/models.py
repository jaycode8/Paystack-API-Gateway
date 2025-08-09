import uuid
from django.db import models

class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=True)
    status = models.CharField(max_length=50)
    paystack_id = models.BigIntegerField(unique=True)  # Paystack transaction ID
    reference = models.CharField(max_length=100, unique=True)
    amount = models.PositiveIntegerField()  # Store in kobo/cents
    currency = models.CharField(max_length=10)
    gateway_response = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField()
    created_at = models.DateTimeField()
    channel = models.CharField(max_length=50)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    product_id = models.UUIDField()
    user_id = models.PositiveIntegerField()
    order_number = models.CharField(max_length=20)
    fees = models.PositiveIntegerField()
    card_type = models.CharField(max_length=50, blank=True, null=True)
    last4 = models.CharField(max_length=4, blank=True, null=True)
    bank = models.CharField(max_length=100, blank=True, null=True)
    customer_email = models.EmailField(blank=True, null=True)
    customer_code = models.CharField(max_length=100)
    created_on = models.DateTimeField(auto_now_add=True)

    def amount_display(self):
        return f"{self.amount:,.2f}"

    def __str__(self):
        return f"{self.order_number} - {self.reference}"

    class Meta:
        db_table = "transaction"
        verbose_name = "transaction"
        verbose_name_plural = "transaction"
        ordering = ["-created_on"]
