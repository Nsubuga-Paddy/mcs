from django.db import models

from .models import WeekProgress

def get_weekly_target(week_number):
    return week_number * 10000

def process_deposit(user_profile, deposit_amount):
    remaining = deposit_amount
    week_number = WeekProgress.objects.filter(user_profile=user_profile).aggregate(
        max_week=models.Max('week_number')
    )['max_week'] or 0

    results = []

    while remaining > 0 and week_number < 52:
        week_number += 1
        expected = get_weekly_target(week_number)

        wp, _ = WeekProgress.objects.get_or_create(
            user_profile=user_profile,
            week_number=week_number,
            defaults={'expected_amount': expected}
        )

        if wp.is_fully_paid:
            continue

        to_pay = expected - wp.amount_paid

        if remaining >= to_pay:
            wp.amount_paid += to_pay
            wp.is_fully_paid = True
            remaining -= to_pay
        else:
            wp.amount_paid += remaining
            remaining = 0

        wp.save()
        results.append({
            'week': week_number,
            'paid': wp.amount_paid,
            'expected': expected,
            'status': 'full' if wp.is_fully_paid else 'partial'
        })

    return results
