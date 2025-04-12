from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import SignUpForm, CustomAuthenticationForm
from .models import SavingsTransaction, UserProfile
from django.db.models import Max, Sum, Count, Q
import json
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_protect
from django.utils.safestring import mark_safe
from django.db import models
from decimal import Decimal
import csv
from django.http import HttpResponse, JsonResponse
from datetime import datetime
from django.utils.timezone import localtime

def index(request):
    return render(request, 'tgfs/index.html')


def signup_view(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Signup successful. Please wait for an admin to approve your account.")
            return redirect("tgfs:login")
    else:
        form = SignUpForm()
    return render(request, "tgfs/signup.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Login successful.")
            return redirect("tgfs:dashboard")
        else:

           pass
    else:
        form = CustomAuthenticationForm()
    return render(request, "tgfs/login.html", {"form": form})


@csrf_protect
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have been logged out successfully.")
        return redirect("tgfs:index")
    return redirect("tgfs:dashboard")


@login_required
def dashboard_view(request):
    # Calculate total savings across all users
    total_group_savings = SavingsTransaction.objects.aggregate(
        total=Sum('amount'))['total'] or Decimal('0')

    total_group_savings_float = float(total_group_savings)

    # Pass data to both Python and JavaScript contexts
    context = {
        'total_group_savings': total_group_savings_float,
        'dashboard_data': mark_safe(json.dumps({
            'total_group_savings': total_group_savings_float
        }))
    }
    
    return render(request, 'tgfs/dashboard.html', context)


def get_weekly_targets():
    """Generate list of weekly targets"""
    return [week * 10000 for week in range(1, 53)]

def evaluate_deposit(deposit, current_week, carry_forward):
    """
    Evaluate a deposit against weekly targets
    deposit: new amount being deposited
    current_week: the next week to be covered
    carry_forward: any balance from previous deposit
    """
    weekly_targets = get_weekly_targets()
    balance = deposit + carry_forward  # Add new deposit to any carried forward balance
    fully_covered = []

    # Start checking from current_week
    for i in range(current_week - 1, 52):
        target = weekly_targets[i]  # Get target for this week (week × 10,000)
        if balance >= target:
            fully_covered.append(i + 1)  # Week is fully covered
            balance -= target  # Subtract the week's target from balance
            current_week += 1  # Move to next week
        else:
            break  # Not enough balance to cover next week

    return {
        'fully_covered_weeks': fully_covered,
        'next_week': current_week,
        'remaining_balance': balance
    }



def process_user_deposit(user_profile, deposit_amount):
    latest_txn = SavingsTransaction.objects.filter(
        user_profile=user_profile
    ).order_by('-date_saved').first()

    if latest_txn:
        current_week = latest_txn.next_week
        carry_forward = float(latest_txn.remaining_balance)
        cumulative_total = float(latest_txn.cumulative_total) + deposit_amount
    else:
        current_week = 1
        carry_forward = 0
        cumulative_total = deposit_amount

    result = evaluate_deposit(deposit_amount, current_week, carry_forward)

    result.update({
        'cumulative_total': cumulative_total
    })

    return result



@login_required
def member_dashboard_view(request):
    user_profile = UserProfile.objects.get(user=request.user)
    
    # Get all transactions ordered by date
    transactions = SavingsTransaction.objects.filter(
        user_profile=user_profile
    ).order_by('-date_saved')
    
    # Get latest transaction for current state
    latest_txn = transactions.order_by('-next_week', '-date_saved').first()


    if latest_txn:
        total_saved = float(latest_txn.cumulative_total)
        current_week = latest_txn.next_week
        carry_forward = float(latest_txn.remaining_balance)
    else:
        total_saved = 0
        current_week = 1
        carry_forward = 0

    progress_percentage = round((total_saved / 13780000) * 100, 2)

    # Example of how the progressive calculation works
    weekly_targets = get_weekly_targets()
    current_week_target = weekly_targets[current_week - 1] if current_week <= 52 else 0

    # Prepare transaction data for display
    updated_transactions = []
    for t in transactions:
        # Format weeks covered for display
        if t.fully_covered_weeks:
            weeks_text = "Weeks: " + ", ".join(map(str, t.fully_covered_weeks))
            status = 'Complete'
        else:
            weeks_text = "No weeks fully covered"
            status = 'Partial'
        
        updated_transactions.append({
            'date_saved': t.date_saved.strftime('%b %d, %Y'),
            'amount': float(t.amount),
            'cumulative_total': float(t.cumulative_total),
            'weeks_covered': weeks_text,
            'status': status,
            'remaining_balance': float(t.remaining_balance)
        })

    context = {
        'savings_data': {
            'total_saved': total_saved,
            'current_week': current_week,
            'carry_forward': carry_forward,
            'target_amount': 13780000,
            'progress_percentage': progress_percentage,
            'current_week_target': current_week_target  # Show target for current week
        },
        'transactions': updated_transactions,
        'member_data_json': mark_safe(json.dumps({
            'totalSaved': total_saved,
            'currentWeek': current_week,
            'carryForward': carry_forward,
            'targetAmount': 13780000,
            'progressPercentage': progress_percentage,
            'transactions': updated_transactions
        }))
    }

    return render(request, 'tgfs/member-dashboard.html', context)

@login_required
def members_view(request):
    return render(request, 'tgfs/members.html')

@login_required
def download_savings(request):
    # Create the HttpResponse object with CSV header
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response['Content-Disposition'] = f'attachment; filename="savings_history_{timestamp}.csv"'

    # Create CSV writer
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Date', 
        'Amount Deposited', 
        'Cumulative Total', 
        'Weeks Covered', 
        'Status', 
        'Balance Forward'
    ])

    # Get user's transactions
    user_profile = UserProfile.objects.get(user=request.user)
    transactions = SavingsTransaction.objects.filter(
        user_profile=user_profile
    ).order_by('-date_saved')

    # Write data rows
    for transaction in transactions:
        status = 'Complete' if (transaction.fully_covered_weeks and 
                              transaction.next_week > transaction.fully_covered_weeks[-1]) else 'Pending'
        
        writer.writerow([
            transaction.date_saved.strftime('%Y-%m-%d'),
            f'{float(transaction.amount):,.0f}',
            f'{float(transaction.cumulative_total):,.0f}',
            ', '.join(map(str, transaction.fully_covered_weeks)) if transaction.fully_covered_weeks else '',
            status,
            f'{float(transaction.remaining_balance):,.0f}'
        ])

    return response


@login_required
def weekly_group_savings_data(request):
    weekly_data = []
    weekly_targets = get_weekly_targets()  # [10000, 20000, ..., 520000]

    for week_number in range(1, 53):
        week_target = weekly_targets[week_number - 1]

        # Get unique user_profiles who fully covered this week
        covered_users = SavingsTransaction.objects.filter(
            fully_covered_weeks__contains=[week_number]
        ).values('user_profile').distinct()

        member_count = covered_users.count()
        expected_total = member_count * week_target

        status = "Complete" if member_count >= 10 else "Pending"
        investment_status = "Invested" if expected_total >= 25000000 else "Not Yet"

        weekly_data.append({
            'week': week_number,
            'total_amount': f"UGX {expected_total:,.0f}",
            'members_contributed': member_count,
            'status': status,
            'investment_status': investment_status
        })

    return JsonResponse({'data': weekly_data})



@login_required
def search_members(request):
    query = request.GET.get('q', '').strip()
    results = []

    if query:
        profiles = UserProfile.objects.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(whatsapp_number__icontains=query)
        ).select_related('user')[:10]

        for profile in profiles:
            transactions = SavingsTransaction.objects.filter(
                user_profile=profile
            ).order_by('-date_saved')

            latest_txn = transactions.order_by('-next_week', '-date_saved').first()

            total_saved = float(latest_txn.cumulative_total) if latest_txn else 0
            fully_covered_weeks = latest_txn.fully_covered_weeks if latest_txn else []
            last_contribution = localtime(latest_txn.date_saved).strftime('%b %d, %Y') if latest_txn else "N/A"
            progress = round((total_saved / 13780000) * 100, 2) if total_saved else 0

            results.append({
                'member_name': f"{profile.user.first_name} {profile.user.last_name}",
                'total_savings': f"UGX {total_saved:,.0f}",
                'weeks_covered': len(fully_covered_weeks),
                'progress': f"{progress}%",
                'last_contribution': last_contribution,
                'status': "Verified" if profile.is_verified else "Pending"
            })


    return JsonResponse({'results': results})


@login_required
def all_members_data(request):
    profiles = UserProfile.objects.select_related('user')
    total_members = profiles.count()

    results = []
    total_savings = 0
    total_weeks_covered = 0

    for profile in profiles:
        transactions = SavingsTransaction.objects.filter(
            user_profile=profile
        ).order_by('-date_saved')

        latest_txn = transactions.order_by('-next_week', '-date_saved').first()

        total_saved = float(latest_txn.cumulative_total) if latest_txn else 0
        fully_covered_weeks = latest_txn.fully_covered_weeks if latest_txn else []

        total_savings += total_saved
        total_weeks_covered += len(fully_covered_weeks)

        results.append({
            'member_name': f"{profile.user.first_name} {profile.user.last_name}",
            'total_savings': f"UGX {total_saved:,.0f}",
            'weeks_covered': len(fully_covered_weeks),
            'progress': f"{round((total_saved / 13780000) * 100, 2)}%",
            'last_contribution': latest_txn.date_saved.strftime('%b %d, %Y') if latest_txn else "N/A",
            'status': "Verified" if profile.is_verified else "Pending"
        })

    # Calculate averages
    average_savings = round(total_savings / total_members, 2) if total_members else 0
    average_weeks = round(total_weeks_covered / total_members, 2) if total_members else 0

    return JsonResponse({
        'results': results,
        'stats': {
            'total_members': total_members,
            'average_savings': average_savings,
            'average_weeks': average_weeks
        }
    })



