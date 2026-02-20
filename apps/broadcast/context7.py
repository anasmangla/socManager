from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings


@dataclass
class Context7Result:
    success: bool
    status_code: int
    payload: dict


class Context7Client:
    """Lightweight wrapper to notify Context7 about campaign events."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or settings.CONTEXT7_API_KEY
        self.base_url = (base_url or settings.CONTEXT7_BASE_URL).rstrip('/')

    def publish_event(self, event_name: str, payload: dict) -> Context7Result:
        if not self.api_key:
            return Context7Result(success=False, status_code=0, payload={'error': 'Missing CONTEXT7_API_KEY'})

        response = requests.post(
            f'{self.base_url}/events',
            json={'event': event_name, 'payload': payload},
            headers={'Authorization': f'Bearer {self.api_key}'},
            timeout=10,
        )
        body = response.json() if response.content else {}
        return Context7Result(success=response.ok, status_code=response.status_code, payload=body)
