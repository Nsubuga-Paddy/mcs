from decimal import Decimal
from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

import math



class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    whatsapp_number = PhoneNumberField(region="UG", unique=True, null=True, blank=True, default="")
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def get_total_savings(self):
        return self.savings_transactions.aggregate(total=Sum('amount'))['total'] or Decimal(0)



class SavingsTransaction(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='savings_transactions')
    amount = models.PositiveIntegerField(default=0)
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
