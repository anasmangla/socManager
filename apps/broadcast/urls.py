from django.urls import path

from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('wizard/accounts/', views.wizard_accounts, name='wizard_accounts'),
    path('campaigns/', views.create_campaign, name='create_campaign'),
    path('campaigns/<int:campaign_id>/send/', views.send_campaign, name='send_campaign'),
    path('campaigns/compose-send/', views.compose_and_send_campaign, name='compose_and_send_campaign'),
]
