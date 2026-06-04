from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class Event(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')
    name = models.CharField(max_length=200)
    scheduled_date = models.DateTimeField()
    location = models.CharField(max_length=255)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    advanced_rs = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    pending_rs = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    total_rs = models.DecimalField(max_digits=12, decimal_places=2, default=0.0, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Automatically calculate total rupees as advanced + pending
        if self.advanced_rs is None:
            self.advanced_rs = Decimal('0.00')
        if self.pending_rs is None:
            self.pending_rs = Decimal('0.00')

        # Detect if pending_rs was set to 0 during an edit
        if self.pk:
            original = Event.objects.get(pk=self.pk)
            if self.pending_rs == 0 and original.pending_rs > 0:
                self.advanced_rs = original.total_rs

        self.total_rs = self.advanced_rs + self.pending_rs
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.status})"

    class Meta:
        ordering = ['-scheduled_date']

