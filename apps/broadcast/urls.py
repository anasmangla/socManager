from django.urls import path

from . import views

urlpatterns = [
    path('health/', views.health, name='health'),
    path('campaigns/', views.create_campaign, name='create_campaign'),
    path('campaigns/<int:campaign_id>/send/', views.send_campaign, name='send_campaign'),
]
