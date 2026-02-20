import logging

import requests
from django.db import DatabaseError
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .api_utils import api_response, db_error_response, json_body, log_audit
from .constants import MAX_PAGE_SIZE, DEFAULT_PAGE_SIZE
from .models import MessageCampaign, SocialAccount
from .security import escape_html, safe_int
from .services import MessageDispatcher
from .validators import (
    ValidationError,
    validate_ai_compose_payload,
    validate_compose_send_payload,
    validate_create_campaign_payload,
)
from .ai_services import NewsScanner, OpenAIContentStudio

logger = logging.getLogger(__name__)


@require_GET
def health(_: HttpRequest) -> JsonResponse:
    return api_response(ok=True, message='Social Manager API healthy', data={'service': 'Social Manager API'})


@ensure_csrf_cookie
@require_GET
def campaign_wizard(request: HttpRequest):
    return render(request, 'broadcast/campaign_wizard.html')


@require_GET
def wizard_accounts(request: HttpRequest) -> JsonResponse:
    page = safe_int(request.GET.get('page'), default=1, minimum=1)
    page_size = safe_int(request.GET.get('page_size'), default=DEFAULT_PAGE_SIZE, minimum=1, maximum=MAX_PAGE_SIZE)
    search = (request.GET.get('q') or '').strip()

    try:
        queryset = SocialAccount.objects.filter(is_active=True)
        if search:
            queryset = queryset.filter(name__icontains=search)

        total = queryset.count()
        offset = (page - 1) * page_size
        accounts = queryset.values('name', 'platform', 'handle')[offset : offset + page_size]

        grouped: dict[str, list[dict[str, str]]] = {}
        for account in accounts:
            grouped.setdefault(account['name'], []).append(
                {'platform': account['platform'], 'handle': escape_html(account['handle'])}
            )

        data = {
            'accounts': grouped,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total': total,
                'has_next': offset + page_size < total,
            },
        }
        return api_response(ok=True, message='Accounts loaded', data=data)
    except DatabaseError as exc:
        return db_error_response(request, action='wizard_accounts', exc=exc)


@csrf_protect
@require_POST
def create_campaign(request: HttpRequest) -> JsonResponse:
    try:
        payload = validate_create_campaign_payload(json_body(request))
    except ValidationError as exc:
        return api_response(ok=False, message=str(exc), status_code=400)

    try:
        campaign = MessageCampaign.objects.create(
            title=payload['title'],
            message=payload['message'],
            status='scheduled' if payload['send_at'] else 'draft',
            send_at=payload['send_at'],
        )
        log_audit(
            request=request,
            action='campaign.create',
            entity='MessageCampaign',
            entity_id=campaign.id,
            changes={'title': campaign.title, 'status': campaign.status},
        )
    except DatabaseError as exc:
        return db_error_response(request, action='create_campaign', exc=exc)

    return api_response(
        ok=True,
        message='Campaign created',
        data={'campaign_id': campaign.id, 'status': campaign.status},
        status_code=201,
    )


@csrf_protect
@require_POST
def send_campaign(request: HttpRequest, campaign_id: int) -> JsonResponse:
    try:
        campaign = MessageCampaign.objects.filter(id=campaign_id).first()
        if campaign is None:
            return api_response(ok=False, message='Campaign not found', status_code=404)

        dispatcher = MessageDispatcher()
        stats = dispatcher.dispatch_campaign(campaign)
        log_audit(
            request=request,
            action='campaign.send',
            entity='MessageCampaign',
            entity_id=campaign.id,
            changes={'status': campaign.status, 'stats': stats},
        )
    except DatabaseError as exc:
        return db_error_response(request, action='send_campaign', exc=exc)

    return api_response(
        ok=True,
        message='Campaign dispatched',
        data={'campaign_id': campaign.id, 'status': campaign.status, 'stats': stats},
    )


@csrf_protect
@require_POST
def compose_and_send_campaign(request: HttpRequest) -> JsonResponse:
    try:
        payload = validate_compose_send_payload(json_body(request))
    except ValidationError as exc:
        return api_response(ok=False, message=str(exc), status_code=400)

    try:
        accounts = SocialAccount.objects.filter(
            is_active=True,
            name__in=payload['account_names'],
            platform__in=payload['platforms'],
        )
        if not accounts.exists():
            return api_response(ok=False, message='No active account match for your selection', status_code=400)

        campaign = MessageCampaign.objects.create(
            title=payload['title'],
            message=payload['message'],
            status='draft',
        )
        dispatcher = MessageDispatcher()
        stats = dispatcher.dispatch_campaign(campaign, accounts=accounts)
        targets = [f'{item.name} on {item.get_platform_display()} (@{item.handle})' for item in accounts]
        log_audit(
            request=request,
            action='campaign.compose_send',
            entity='MessageCampaign',
            entity_id=campaign.id,
            changes={'status': campaign.status, 'targets': targets},
        )
    except DatabaseError as exc:
        return db_error_response(request, action='compose_and_send_campaign', exc=exc)

    return api_response(
        ok=True,
        message='Campaign posted successfully',
        data={
            'campaign_id': campaign.id,
            'status': campaign.status,
            'stats': stats,
            'targets': targets,
        },
    )


@csrf_protect
@require_POST
def ai_compose_campaign(request: HttpRequest) -> JsonResponse:
    try:
        payload = validate_ai_compose_payload(json_body(request))
    except ValidationError as exc:
        return api_response(ok=False, message=str(exc), status_code=400)

    scanner = NewsScanner()
    studio = OpenAIContentStudio()

    try:
        articles = scanner.fetch(keywords=payload['keywords'], area=payload['area'])
        generated = studio.compose_post(
            keywords=payload['keywords'],
            area=payload['area'],
            business_perspective=payload['business_perspective'],
            articles=articles,
        )
        image_url = studio.generate_image(generated.get('image_prompt', ''))
    except requests.RequestException:
        logger.exception('AI/news provider failed')
        return api_response(ok=False, message='AI/news provider temporarily unavailable', status_code=502)

    try:
        campaign = MessageCampaign.objects.create(
            title=(generated.get('title') or f"{payload['keywords'].title()} update")[:200],
            message=generated.get('message') or '',
            image_url=image_url,
            source_type='ai_news',
            task_mode=payload['task_mode'],
            status='scheduled' if payload['send_at'] and payload['task_mode'] == 'automated' else 'draft',
            send_at=payload['send_at'] if payload['task_mode'] == 'automated' else None,
            metadata={
                'keywords': payload['keywords'],
                'area': payload['area'],
                'business_perspective': payload['business_perspective'],
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

        should_dispatch = payload['autopost'] and payload['account_names'] and payload['platforms']
        if should_dispatch:
            accounts = SocialAccount.objects.filter(
                is_active=True,
                name__in=payload['account_names'],
                platform__in=payload['platforms'],
            )
            if not accounts.exists():
                return api_response(ok=False, message='No active account match for your selection', status_code=400)
            dispatcher = MessageDispatcher()
            stats = dispatcher.dispatch_campaign(campaign, accounts=accounts)
            response['status'] = campaign.status
            response['stats'] = stats

        log_audit(
            request=request,
            action='campaign.ai_compose',
            entity='MessageCampaign',
            entity_id=campaign.id,
            changes={'status': response['status'], 'task_mode': campaign.task_mode},
        )
    except DatabaseError as exc:
        return db_error_response(request, action='ai_compose_campaign', exc=exc)

    return api_response(ok=True, message='Campaign generated', data=response, status_code=201)
