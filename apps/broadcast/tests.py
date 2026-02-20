import json

from django.test import Client, TestCase

from apps.broadcast.models import SocialAccount


class BroadcastViewTests(TestCase):
    def setUp(self):
        self.csrf_client = Client(enforce_csrf_checks=True)

    def test_create_campaign_requires_csrf(self):
        response = self.csrf_client.post(
            '/api/campaigns/',
            data=json.dumps({'title': 'T', 'message': 'M'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_wizard_accounts_returns_contract_with_pagination(self):
        SocialAccount.objects.create(
            name='Acme',
            platform='x',
            handle='acme',
            access_token='token',
            is_active=True,
        )
        response = self.client.get('/api/wizard/accounts/?page=1&page_size=10')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['status'], 'success')
        self.assertIn('data', payload)
        self.assertIn('pagination', payload['data'])
