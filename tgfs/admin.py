from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, SavingsTransaction
from django.utils.html import format_html

# Inline UserProfile Editing inside User Admin Panel
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ('whatsapp_number', 'is_verified')

class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# UserProfile Admin
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_username', 'get_first_name', 'get_last_name', 
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

# SavingsTransaction Admin
@admin.register(SavingsTransaction)
class SavingsTransactionAdmin(admin.ModelAdmin):
    list_display = ('user_profile', 'formatted_amount', 'formatted_weeks', 
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
            'fields': ('user_profile', 'amount')
        }),
        ('Progress Details', {
            'fields': ('date_saved', 'cumulative_total', 'fully_covered_weeks', 
                      'next_week', 'remaining_balance')
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:  # If this is a new transaction
            # Process the deposit using our logic
            from .views import process_user_deposit
            result = process_user_deposit(obj.user_profile, obj.amount)
            
            # Update the object with the results
            obj.fully_covered_weeks = result['fully_covered_weeks']
            obj.next_week = result['next_week']
            obj.remaining_balance = result['remaining_balance']
            obj.cumulative_total = result['cumulative_total']

        super().save_model(request, obj, form, change)
        
       