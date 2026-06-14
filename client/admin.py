from django.contrib import admin
from .models import UserProfile, PaymentRequest, LicenseKey


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'credits')
    search_fields = ('user__username',)
    readonly_fields = ('user',)


@admin.register(PaymentRequest)
class PaymentRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'utr', 'credits_requested', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'utr')
    actions = ['approve_payment']
    readonly_fields = ('created_at',)

    def approve_payment(self, request, queryset):
        for payment in queryset.filter(status='pending'):
            profile, _ = UserProfile.objects.get_or_create(user=payment.user)
            profile.credits += payment.credits_requested
            profile.save()
            payment.status = 'approved'
            payment.save()
        self.message_user(request, "✅ Payments approved! Credits added.")
    
    approve_payment.short_description = "✅ Approve & Add Credits"


@admin.register(LicenseKey)
class LicenseKeyAdmin(admin.ModelAdmin):
    list_display = ('user', 'key', 'days', 'credits_used', 'created_at')
    search_fields = ('user__username', 'key')
    readonly_fields = ('created_at', 'key')
