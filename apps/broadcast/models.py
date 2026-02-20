from django.db import models
from django.utils import timezone


class SocialAccount(models.Model):
    PLATFORM_CHOICES = [
        ('x', 'X / Twitter'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('linkedin', 'LinkedIn'),
        ('tiktok', 'TikTok'),
    ]

    name = models.CharField(max_length=120)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    handle = models.CharField(max_length=120)
    access_token = models.TextField(help_text='Store securely in production (vault/secret manager).')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('platform', 'handle')

    def __str__(self) -> str:
        return f"{self.get_platform_display()} - @{self.handle}"


class MessageCampaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    title = models.CharField(max_length=200)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    send_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_ready_to_send(self) -> bool:
        if self.status not in {'draft', 'scheduled'}:
            return False
        if self.send_at is None:
            return True
        return self.send_at <= timezone.now()

    def __str__(self) -> str:
        return self.title


class DeliveryLog(models.Model):
    campaign = models.ForeignKey(MessageCampaign, related_name='deliveries', on_delete=models.CASCADE)
    account = models.ForeignKey(SocialAccount, related_name='deliveries', on_delete=models.CASCADE)
    success = models.BooleanField(default=False)
    provider_message_id = models.CharField(max_length=255, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.campaign.title} -> {self.account.handle}"
