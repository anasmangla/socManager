from __future__ import annotations

from dataclasses import dataclass

import requests
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


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
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods={'POST'},
        )
        adapter = HTTPAdapter(max_retries=retries)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    def publish_event(self, event_name: str, payload: dict) -> Context7Result:
        if not self.api_key:
            return Context7Result(success=False, status_code=0, payload={'error': 'Missing CONTEXT7_API_KEY'})

        try:
            response = self._session.post(
                f'{self.base_url}/events',
                json={'event': event_name, 'payload': payload},
                headers={'Authorization': f'Bearer {self.api_key}'},
                timeout=10,
            )
        except requests.RequestException as exc:
            return Context7Result(
                success=False,
                status_code=0,
                payload={'error': 'Request to Context7 failed', 'detail': str(exc)},
            )

        try:
            body = response.json() if response.content else {}
        except ValueError:
            body = {'error': 'Invalid JSON response from Context7', 'raw_body': response.text[:500]}

        return Context7Result(success=response.ok, status_code=response.status_code, payload=body)
