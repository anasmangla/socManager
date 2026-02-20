from django.contrib import admin

from .models import (
    BusinessAccount,
    BusinessCredential,
    DeliveryLog,
    MessageCampaign,
    SocialAccount,
    SocialAPICredential,
)


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'platform', 'handle', 'is_active', 'created_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('name', 'handle')


@admin.register(BusinessAccount)
class BusinessAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'contact_email', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'contact_email')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(BusinessCredential)
class BusinessCredentialAdmin(admin.ModelAdmin):
    list_display = ('business', 'label', 'username', 'is_active', 'updated_at')
    list_filter = ('is_active', 'business')
    search_fields = ('business__name', 'label', 'username')


@admin.register(SocialAPICredential)
class SocialAPICredentialAdmin(admin.ModelAdmin):
    list_display = ('platform', 'app_name', 'client_id', 'is_active', 'updated_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('app_name', 'client_id')


@admin.register(MessageCampaign)
class MessageCampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'send_at', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('title', 'message')


@admin.register(DeliveryLog)
class DeliveryLogAdmin(admin.ModelAdmin):
    list_display = ('campaign', 'account', 'success', 'provider_message_id', 'created_at')
    list_filter = ('success', 'account__platform')
    search_fields = ('campaign__title', 'account__handle', 'error_message')
