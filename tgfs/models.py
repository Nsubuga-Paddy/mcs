from decimal import Decimal
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

import math



class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    account_number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        help_text="Auto-generated: MCSTGF-<Initials><0001…>"
    )
    whatsapp_number = PhoneNumberField(region="UG", unique=True, null=True, blank=True, default="")
    is_verified = models.BooleanField(default=False)

    def get_total_savings(self):
        return self.savings_transactions.aggregate(total=Sum('amount'))['total'] or Decimal(0)


    def save(self, *args, **kwargs):
        # only generate once, when empty
        if not self.account_number:
            initials = (
                f"{self.user.last_name[:1]}{self.user.first_name[:1]}"
            ).upper()            # e.g. "NP"
            prefix   = "MCSTGF"

            # count how many joined earlier
            earlier = UserProfile.objects.filter(
                user__date_joined__lt=self.user.date_joined
            ).count()
            seq = earlier + 1     # 1-based
            seq_str = str(seq).zfill(4)    # "0001", "0002", …

            self.account_number = f"{prefix}-{initials}{seq_str}"

            # Use an atomic block so that two simultaneous saves don’t collide
            with transaction.atomic():
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)


    def __str__(self):
        return self.user.username

    


class SavingsTransaction(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='savings_transactions')
    amount = models.PositiveIntegerField(default=0)
    receipt_number = models.CharField(max_length=20, blank=True, null=True, help_text="Receipt number for this deposit")
    date_saved = models.DateTimeField(default=timezone.now)
    
    cumulative_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fully_covered_weeks = models.JSONField(default=list) 
    next_week = models.PositiveIntegerField(default=1)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ['-date_saved']

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.amount} on {self.date_saved.date()}"



class Investment(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='investments')
    amount_invested = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.FloatField(help_text="Annual interest rate (e.g., 12.5 for 12.5%)")
    maturity_months = models.PositiveIntegerField(default=8)
    date_invested = models.DateField(default=timezone.now)

    @property
    def maturity_date(self):
        return self.date_invested + timedelta(days=30 * self.maturity_months)

    @property
    def interest_expected(self):
        # Using simple interest
        return self.amount_invested * Decimal(self.interest_rate / 100) * Decimal(self.maturity_months / 12)

    @property
    def interest_gained_so_far(self):
        months_elapsed = (timezone.now().date() - self.date_invested).days // 30
        months_elapsed = min(months_elapsed, self.maturity_months)
        return self.amount_invested * Decimal(self.interest_rate / 100) * Decimal(months_elapsed / 12)

    def __str__(self):
        return f"{self.user_profile.user.username} - UGX {self.amount_invested:,.0f} at {self.interest_rate}%"
