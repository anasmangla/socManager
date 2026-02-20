from __future__ import annotations

import json
import logging
from typing import Any

from django.http import HttpRequest, JsonResponse

from .models import AuditLog

logger = logging.getLogger(__name__)


def json_body(request: HttpRequest) -> dict[str, Any]:
    try:
        return json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return {}


def api_response(*, ok: bool, message: str, data: dict[str, Any] | None = None, html: str = '', status_code: int = 200) -> JsonResponse:
    return JsonResponse(
        {
            'status': 'success' if ok else 'error',
            'message': message,
            'html': html,
            'data': data or {},
        },
        status=status_code,
    )


def db_error_response(request: HttpRequest, *, action: str, exc: Exception) -> JsonResponse:
    logger.exception('Database operation failed', extra={'action': action, 'path': request.path})
    return api_response(ok=False, message='We could not complete your request right now. Please try again.', status_code=500)


def log_audit(*, request: HttpRequest, action: str, entity: str, entity_id: int, changes: dict[str, Any] | None = None) -> None:
    actor = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    AuditLog.objects.create(
        actor=actor,
        action=action,
        entity=entity,
        entity_id=entity_id,
        changes=changes or {},
    )
