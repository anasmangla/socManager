from django.contrib import admin

from .models import DeliveryLog, MessageCampaign, SocialAccount


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'platform', 'handle', 'is_active', 'created_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('name', 'handle')


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
