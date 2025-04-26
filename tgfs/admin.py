from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.db.models import Sum
from .models import UserProfile, SavingsTransaction, Investment
from django.utils.html import format_html

# Inline UserProfile Editing inside User Admin Panel
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('account_number', 'whatsapp_number', 'is_verified')
    readonly_fields = ('account_number',)

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


class SavingsTransactionInline(admin.TabularInline):
    model = SavingsTransaction
    extra = 0
    fields = (
       'date_saved',
        'amount',
        'receipt_number',
        'cumulative_total',
        'fully_covered_weeks',        
        'next_week',
        'remaining_balance',
    )
    readonly_fields = (
        'amount',
        'cumulative_total',
        'fully_covered_weeks',
        'next_week',
        'remaining_balance',
        'date_saved',
    )
    
    can_delete = False
    show_change_link = True
    ordering = ['-date_saved']


# UserProfile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_username', 'account_number', 'get_first_name', 'get_last_name', 
                   'get_email', 'whatsapp_number', 'is_verified', 'get_date_joined')
    search_fields = ('user__username', 'user__email', 'whatsapp_number')
    list_filter = ('is_verified', 'user__is_active', 'user__date_joined')
    ordering = ('-user__date_joined',)
    raw_id_fields = ('user',)
    readonly_fields = ('user',)

    def user_username(self, obj):
        return obj.user.username
    user_username.admin_order_field = 'user__username'
    user_username.short_description = 'Username'

    def get_first_name(self, obj):
        return obj.user.first_name
    get_first_name.admin_order_field = 'user__first_name'
    get_first_name.short_description = 'First Name'

    def get_last_name(self, obj):
        return obj.user.last_name
    get_last_name.admin_order_field = 'user__last_name'
    get_last_name.short_description = 'Last Name'

    def get_email(self, obj):
        return obj.user.email
    get_email.admin_order_field = 'user__email'
    get_email.short_description = 'Email'

    def get_date_joined(self, obj):
        return obj.user.date_joined.strftime('%Y-%m-%d %H:%M:%S')
    get_date_joined.admin_order_field = 'user__date_joined'
    get_date_joined.short_description = 'Date Joined'

    def get_total_savings(self, obj):
        total = SavingsTransaction.objects.filter(user_profile=obj).aggregate(
            total=Sum('amount'))['total'] or 0
        return f"UGX {total:,.0f}"
    get_total_savings.short_description = "Cumulative Savings"

    inlines = [SavingsTransactionInline]

# SavingsTransaction Admin
@admin.register(SavingsTransaction)
class SavingsTransactionAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'formatted_amount', 'receipt_number', 'formatted_weeks', 
                   'formatted_next_week', 'formatted_balance', 'date_saved')
    
    list_filter = ('date_saved', 'user_profile__user__is_active')
    
    search_fields = ('user_profile__user__username', 'user_profile__user__first_name')
    
    date_hierarchy = 'date_saved'
    
    autocomplete_fields = ('user_profile',)
    
    readonly_fields = ('cumulative_total', 'fully_covered_weeks', 'next_week', 
                      'remaining_balance')

    def formatted_amount(self, obj):
        return f"UGX {obj.amount:,.0f}" if obj.amount else "UGX 0"
    formatted_amount.short_description = 'Amount Saved'

    def formatted_weeks(self, obj):
        if not obj.fully_covered_weeks:
            return "No weeks fully covered"
        weeks = ", ".join(map(str, obj.fully_covered_weeks))
        return f"Weeks: {weeks}"
    formatted_weeks.short_description = "Weeks Covered"

    def formatted_next_week(self, obj):
        return f"Week {obj.next_week}"
    formatted_next_week.short_description = "Next Week"

    def formatted_balance(self, obj):
        return f"UGX {float(obj.remaining_balance):,.0f}"
    formatted_balance.short_description = "Balance Forward"

    fieldsets = (
        ('Basic Information', {
            'fields': ('user_profile', 'amount', 'receipt_number')
        }),
        ('Progress Details', {
            'fields': ('date_saved', 'cumulative_total', 'fully_covered_weeks', 
                      'next_week', 'remaining_balance')
        })
    )

    def save_model(self, request, obj, form, change):
        # Always recalculate everything from scratch
        from .models import SavingsTransaction
        from .views import evaluate_deposit, get_weekly_targets

        # Recalculate all transactions in ascending order by date_saved
        previous_transactions = SavingsTransaction.objects.filter(
            user_profile=obj.user_profile
        ).exclude(pk=obj.pk).order_by('date_saved')


        cumulative_total = 0
        carry_forward = 0
        current_week = 1

        # Recalculate all prior transactions first
        for txn in previous_transactions:
            result = evaluate_deposit(txn.amount, current_week, carry_forward)
            cumulative_total += txn.amount
            txn.fully_covered_weeks = result['fully_covered_weeks']
            txn.next_week = result['next_week']
            txn.remaining_balance = result['remaining_balance']
            txn.cumulative_total = cumulative_total
            carry_forward = float(txn.remaining_balance)
            current_week = result['next_week']
            txn.save()

        # Now calculate for the current (new or edited) transaction
        result = evaluate_deposit(obj.amount, current_week, carry_forward)
        cumulative_total += obj.amount
        obj.fully_covered_weeks = result['fully_covered_weeks']
        obj.next_week = result['next_week']
        obj.remaining_balance = result['remaining_balance']
        obj.cumulative_total = cumulative_total

        super().save_model(request, obj, form, change)


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'amount_invested', 'interest_rate', 'maturity_months', 'date_invested', 'maturity_date', 'interest_expected', 'interest_gained_so_far')
    list_filter = ('date_invested', 'maturity_months')
    search_fields = ('user_profile__user__username', 'user_profile__user__first_name')
    autocomplete_fields = ('user_profile',)

       