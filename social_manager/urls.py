from django.contrib import admin
from django.urls import include, path

from apps.broadcast.views import campaign_wizard

urlpatterns = [
    path('', campaign_wizard, name='home'),
    path('admin/', admin.site.urls),
    path('api/', include('apps.broadcast.urls')),
]
