from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.broadcast.models import MessageCampaign
from apps.broadcast.services import MessageDispatcher


class Command(BaseCommand):
    help = 'Dispatch campaigns that are scheduled and ready to send.'

    def handle(self, *args, **options):
        now = timezone.now()
        ready_campaigns = MessageCampaign.objects.filter(status='scheduled', send_at__lte=now)

        dispatcher = MessageDispatcher()
        for campaign in ready_campaigns:
            stats = dispatcher.dispatch_campaign(campaign)
            self.stdout.write(self.style.SUCCESS(f'Dispatched campaign {campaign.id}: {stats}'))

        if not ready_campaigns.exists():
            self.stdout.write('No scheduled campaigns were ready to send.')
