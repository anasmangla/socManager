# Social Manager (Django + Context7)

Starter backend for a Python-based **Social Manager** platform that can:
- Store social media account API credentials.
- Create campaigns to send one message to all connected social accounts.
- Schedule future sends.
- Emit campaign events to Context7.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Initial API endpoints

- `GET /api/health/` - service health check.
- `POST /api/campaigns/` - create campaign.
  - Payload:
    ```json
    {
      "title": "Launch Promo",
      "message": "Hello from Social Manager!",
      "send_at": "2026-01-01T12:00:00Z"
    }
    ```
- `POST /api/campaigns/<id>/send/` - dispatch immediately to all active accounts.
- `POST /api/campaigns/compose-send/` - create and dispatch to selected account names + platforms.
- `POST /api/campaigns/ai-compose/` - scan news + generate copy/image with OpenAI, then save/post as manual or automated task.
  - Payload:
    ```json
    {
      "keywords": "mortgage rates",
      "area": "Texas",
      "business_perspective": "We help buyers lock options confidently.",
      "task_mode": "manual",
      "send_at": "2026-01-01T12:00:00Z",
      "autopost": true,
      "account_names": ["Acme Realty"],
      "platforms": ["facebook", "linkedin"]
    }
    ```

## Scheduling

Run this periodically (cron/Celery beat) to send campaigns when `send_at` is due:

```bash
python manage.py dispatch_scheduled_messages
```

## Notes

- Provider integrations are intentionally stubbed in `apps/broadcast/services.py` for now.
- Context7 is wired via `apps/broadcast/context7.py` and uses `CONTEXT7_API_KEY` / `CONTEXT7_BASE_URL`.
- Use the Django admin (`/admin`) to manage social accounts, business credentials, social API credentials, and delivery logs.
