from unittest.mock import MagicMock, patch

import requests
from django.test import SimpleTestCase

from apps.broadcast.context7 import Context7Client


class Context7ClientTests(SimpleTestCase):
    def test_publish_event_returns_error_without_api_key(self):
        client = Context7Client(api_key='')

        result = client.publish_event('campaign.dispatched', {'campaign_id': 1})

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 0)
        self.assertEqual(result.payload['error'], 'Missing CONTEXT7_API_KEY')

    @patch('apps.broadcast.context7.requests.Session.post')
    def test_publish_event_handles_transport_error(self, mock_post):
        mock_post.side_effect = requests.RequestException('network issue')
        client = Context7Client(api_key='token')

        result = client.publish_event('campaign.dispatched', {'campaign_id': 1})

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 0)
        self.assertEqual(result.payload['error'], 'Request to Context7 failed')

    @patch('apps.broadcast.context7.requests.Session.post')
    def test_publish_event_handles_invalid_json(self, mock_post):
        response = MagicMock()
        response.ok = False
        response.status_code = 502
        response.content = b'invalid'
        response.text = 'gateway failure'
        response.json.side_effect = ValueError('invalid json')
        mock_post.return_value = response

        client = Context7Client(api_key='token')
        result = client.publish_event('campaign.dispatched', {'campaign_id': 1})

        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 502)
        self.assertEqual(result.payload['error'], 'Invalid JSON response from Context7')
