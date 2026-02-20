from __future__ import annotations

from typing import Any

from .models import MessageCampaign


class ValidationError(Exception):
    pass


def _coerce_text(payload: dict[str, Any], key: str, *, required: bool = False, max_length: int | None = None) -> str:
    value = str(payload.get(key) or '').strip()
    if required and not value:
        raise ValidationError(f'{key} is required')
    if max_length and len(value) > max_length:
        raise ValidationError(f'{key} must be <= {max_length} characters')
    return value


def _coerce_list(payload: dict[str, Any], key: str, *, required: bool = False) -> list[str]:
    raw_value = payload.get(key) or []
    values = [str(item).strip() for item in raw_value if str(item).strip()]
    if required and not values:
        raise ValidationError(f'{key} is required')
    return values


def validate_create_campaign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        'title': _coerce_text(payload, 'title', required=True, max_length=200),
        'message': _coerce_text(payload, 'message', required=True),
        'send_at': payload.get('send_at'),
    }


def validate_compose_send_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        'title': _coerce_text(payload, 'title', required=True, max_length=200),
        'message': _coerce_text(payload, 'message', required=True),
        'account_names': _coerce_list(payload, 'account_names', required=True),
        'platforms': _coerce_list(payload, 'platforms', required=True),
    }


def validate_ai_compose_payload(payload: dict[str, Any]) -> dict[str, Any]:
    task_mode = _coerce_text(payload, 'task_mode') or 'manual'
    if task_mode not in {choice[0] for choice in MessageCampaign.TASK_MODE_CHOICES}:
        raise ValidationError('task_mode must be manual or automated')

    return {
        'keywords': _coerce_text(payload, 'keywords', required=True, max_length=120),
        'area': _coerce_text(payload, 'area', max_length=120),
        'business_perspective': _coerce_text(payload, 'business_perspective', max_length=250),
        'task_mode': task_mode,
        'send_at': payload.get('send_at'),
        'account_names': _coerce_list(payload, 'account_names'),
        'platforms': _coerce_list(payload, 'platforms'),
        'autopost': bool(payload.get('autopost', False)),
    }
