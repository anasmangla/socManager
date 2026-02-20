import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .models import MessageCampaign
from .services import MessageDispatcher


@require_GET
def health(_: HttpRequest) -> JsonResponse:
    return JsonResponse({'service': 'Social Manager API', 'status': 'ok'})


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
