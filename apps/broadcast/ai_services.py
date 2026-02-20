from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import requests
from django.conf import settings


@dataclass
class NewsArticle:
    title: str
    link: str
    source: str
    published_at: str


class NewsScanner:
    def fetch(self, keywords: str, area: str = '', limit: int = 5) -> list[NewsArticle]:
        query = ' '.join(value for value in [keywords.strip(), area.strip()] if value).strip()
        if not query:
            return []

        url = f'https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en'
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        articles: list[NewsArticle] = []

        for item in items[:limit]:
            articles.append(
                NewsArticle(
                    title=(item.findtext('title') or '').strip(),
                    link=(item.findtext('link') or '').strip(),
                    source=(item.findtext('source') or 'Google News').strip(),
                    published_at=(item.findtext('pubDate') or '').strip(),
                )
            )

        return articles


class OpenAIContentStudio:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.chat_model = settings.OPENAI_CHAT_MODEL
        self.image_model = settings.OPENAI_IMAGE_MODEL

    def compose_post(
        self,
        keywords: str,
        area: str,
        business_perspective: str,
        articles: list[NewsArticle],
    ) -> dict:
        if not self.api_key:
            return self._fallback_copy(keywords, area, business_perspective, articles)

        headlines = '\n'.join(f'- {article.title}' for article in articles) or '- No headlines available'
        system_prompt = (
            'You are a social media strategist. Write concise, positive social content from a business perspective. '
            'Return JSON with keys: title, message, image_prompt.'
        )
        user_prompt = (
            f'Keywords: {keywords}\n'
            f'Area: {area or "General"}\n'
            f'Business perspective: {business_perspective}\n'
            f'Headlines:\n{headlines}'
        )

        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': self.chat_model,
                'response_format': {'type': 'json_object'},
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
                'temperature': 0.7,
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        content = payload['choices'][0]['message']['content']
        data = json.loads(content)

        return {
            'title': (data.get('title') or '').strip(),
            'message': (data.get('message') or '').strip(),
            'image_prompt': (data.get('image_prompt') or '').strip(),
        }

    def generate_image(self, image_prompt: str) -> str:
        if not image_prompt:
            return ''
        if not self.api_key:
            return ''

        response = requests.post(
            'https://api.openai.com/v1/images/generations',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': self.image_model,
                'prompt': image_prompt,
                'size': '1024x1024',
            },
            timeout=45,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get('data', [{}])[0].get('url', '')

    def _fallback_copy(
        self,
        keywords: str,
        area: str,
        business_perspective: str,
        articles: list[NewsArticle],
    ) -> dict:
        lead = articles[0].title if articles else f'Updates about {keywords}'
        location = area or 'our market'
        return {
            'title': f'{keywords.title()} update for {location}',
            'message': (
                f"{lead}. We are monitoring {keywords} in {location} and helping customers act confidently. "
                f'{business_perspective}'.strip()
            ),
            'image_prompt': (
                f'Professional social graphic about {keywords} in {location}, business style, modern and optimistic, ' 
                f'timestamp {datetime.utcnow().date().isoformat()}'
            ),
        }
