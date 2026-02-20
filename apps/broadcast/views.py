import json

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .models import MessageCampaign, SocialAccount
from .services import MessageDispatcher


@require_GET
def health(_: HttpRequest) -> JsonResponse:
    return JsonResponse({'service': 'Social Manager API', 'status': 'ok'})


@require_GET
def campaign_wizard(request: HttpRequest):
    return render(request, 'broadcast/campaign_wizard.html')


@require_GET
def wizard_accounts(request: HttpRequest) -> JsonResponse:
    accounts = SocialAccount.objects.filter(is_active=True).values('name', 'platform', 'handle')
    grouped = {}

    for account in accounts:
        grouped.setdefault(account['name'], []).append(
            {
                'platform': account['platform'],
                'handle': account['handle'],
            }
        )

    return JsonResponse({'accounts': grouped})


@require_POST
def create_campaign(request: HttpRequest) -> JsonResponse:
    body = json.loads(request.body or '{}')
    title = (body.get('title') or '').strip()
    message = (body.get('message') or '').strip()
    send_at = body.get('send_at')

    if not title or not message:
        return JsonResponse({'error': 'title and message are required'}, status=400)

    campaign = MessageCampaign.objects.create(
        title=title,
        message=message,
        status='scheduled' if send_at else 'draft',
        send_at=send_at,
    )
    return JsonResponse({'id': campaign.id, 'status': campaign.status}, status=201)


@require_POST
def send_campaign(request: HttpRequest, campaign_id: int) -> JsonResponse:
    campaign = MessageCampaign.objects.filter(id=campaign_id).first()
    if campaign is None:
        return JsonResponse({'error': 'campaign not found'}, status=404)

    dispatcher = MessageDispatcher()
    stats = dispatcher.dispatch_campaign(campaign)
    return JsonResponse({'campaign_id': campaign.id, 'status': campaign.status, 'stats': stats})


@require_POST
def compose_and_send_campaign(request: HttpRequest) -> JsonResponse:
    body = json.loads(request.body or '{}')
    title = (body.get('title') or '').strip()
    message = (body.get('message') or '').strip()
    account_names = body.get('account_names') or []
    platforms = body.get('platforms') or []

    if not title or not message:
        return JsonResponse({'error': 'title and message are required'}, status=400)
    if not account_names:
        return JsonResponse({'error': 'Select at least one account'}, status=400)
    if not platforms:
        return JsonResponse({'error': 'Select at least one platform'}, status=400)

    accounts = SocialAccount.objects.filter(
        is_active=True,
        name__in=account_names,
        platform__in=platforms,
    )
    if not accounts.exists():
        return JsonResponse({'error': 'No active account match for your selection'}, status=400)

    campaign = MessageCampaign.objects.create(
        title=title,
        message=message,
        status='draft',
    )
    dispatcher = MessageDispatcher()
    stats = dispatcher.dispatch_campaign(campaign, accounts=accounts)
    return JsonResponse(
        {
            'campaign_id': campaign.id,
            'status': campaign.status,
            'stats': stats,
            'targets': [f"{item.name} on {item.get_platform_display()} (@{item.handle})" for item in accounts],
        }
    )
