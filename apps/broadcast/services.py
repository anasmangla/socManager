from __future__ import annotations

from django.db import transaction

from .context7 import Context7Client
from .models import DeliveryLog, MessageCampaign, SocialAccount


class MessageDispatcher:
    """Dispatches a campaign to every active social account."""

    def __init__(self, context7_client: Context7Client | None = None):
        self.context7_client = context7_client or Context7Client()

    def dispatch_campaign(self, campaign: MessageCampaign) -> dict:
        accounts = SocialAccount.objects.filter(is_active=True)
        stats = {'total': accounts.count(), 'sent': 0, 'failed': 0}

        with transaction.atomic():
            campaign.status = 'sending'
            campaign.save(update_fields=['status', 'updated_at'])

            for account in accounts:
                # Placeholder for real provider adapters (Meta API, X API, LinkedIn API, etc.)
                success, provider_message_id, payload, error_message = self._send_to_provider(campaign.message, account)
                DeliveryLog.objects.create(
                    campaign=campaign,
                    account=account,
                    success=success,
                    provider_message_id=provider_message_id,
                    response_payload=payload,
                    error_message=error_message,
                )
                if success:
                    stats['sent'] += 1
                else:
                    stats['failed'] += 1

            campaign.status = 'sent' if stats['failed'] == 0 else 'failed'
            campaign.save(update_fields=['status', 'updated_at'])

        self.context7_client.publish_event(
            'campaign.dispatched',
            {
                'campaign_id': campaign.id,
                'title': campaign.title,
                'status': campaign.status,
                'stats': stats,
            },
        )
        return stats

    def _send_to_provider(self, message: str, account: SocialAccount) -> tuple[bool, str, dict, str]:
        # Stubbed provider behavior for now.
        payload = {'platform': account.platform, 'handle': account.handle, 'preview': message[:100]}
        return True, f'{account.platform}-{account.id}', payload, ''
