import json

import requests
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .ai_services import NewsScanner, OpenAIContentStudio
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


@require_POST
def ai_compose_campaign(request: HttpRequest) -> JsonResponse:
    body = json.loads(request.body or '{}')
    keywords = (body.get('keywords') or '').strip()
    area = (body.get('area') or '').strip()
    business_perspective = (body.get('business_perspective') or '').strip()
    task_mode = (body.get('task_mode') or 'manual').strip().lower()
    send_at = body.get('send_at')
    account_names = body.get('account_names') or []
    platforms = body.get('platforms') or []
    autopost = bool(body.get('autopost', False))

    if not keywords:
        return JsonResponse({'error': 'keywords are required'}, status=400)
    if task_mode not in {'manual', 'automated'}:
        return JsonResponse({'error': 'task_mode must be manual or automated'}, status=400)

    scanner = NewsScanner()
    studio = OpenAIContentStudio()

    try:
        articles = scanner.fetch(keywords=keywords, area=area)
        generated = studio.compose_post(
            keywords=keywords,
            area=area,
            business_perspective=business_perspective,
            articles=articles,
        )
        image_url = studio.generate_image(generated.get('image_prompt', ''))
    except requests.RequestException as exc:
        return JsonResponse({'error': f'AI/news provider failed: {exc}'}, status=502)

    campaign = MessageCampaign.objects.create(
        title=(generated.get('title') or f'{keywords.title()} update')[:200],
        message=generated.get('message') or '',
        image_url=image_url,
        source_type='ai_news',
        task_mode=task_mode,
        status='scheduled' if send_at and task_mode == 'automated' else 'draft',
        send_at=send_at if task_mode == 'automated' else None,
        metadata={
            'keywords': keywords,
            'area': area,
            'business_perspective': business_perspective,
            'articles': [
                {
                    'title': item.title,
                    'link': item.link,
                    'source': item.source,
                    'published_at': item.published_at,
                }
                for item in articles
            ],
            'image_prompt': generated.get('image_prompt', ''),
        },
    )

    response = {
        'campaign_id': campaign.id,
        'status': campaign.status,
        'title': campaign.title,
        'message': campaign.message,
        'image_url': campaign.image_url,
        'task_mode': campaign.task_mode,
        'articles': campaign.metadata.get('articles', []),
    }

    should_dispatch = autopost and account_names and platforms
    if should_dispatch:
        accounts = SocialAccount.objects.filter(
            is_active=True,
            name__in=account_names,
            platform__in=platforms,
        )
        if not accounts.exists():
            return JsonResponse({'error': 'No active account match for your selection'}, status=400)
        dispatcher = MessageDispatcher()
        stats = dispatcher.dispatch_campaign(campaign, accounts=accounts)
        response['status'] = campaign.status
        response['stats'] = stats

    return JsonResponse(response, status=201)
