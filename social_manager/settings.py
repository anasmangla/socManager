import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {'1', 'true', 'yes', 'on'}


def _env_list(name: str, default: str = '') -> list[str]:
    raw_value = os.getenv(name, default)
    return [item.strip() for item in raw_value.split(',') if item.strip()]


DJANGO_ENV = os.getenv('DJANGO_ENV', 'development').strip().lower()
IS_PRODUCTION = DJANGO_ENV in {'production', 'prod'}

DEBUG = _env_bool('DJANGO_DEBUG', default=False)

_secret_key = os.getenv('DJANGO_SECRET_KEY', '').strip()
if _secret_key:
    SECRET_KEY = _secret_key
elif IS_PRODUCTION:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY must be configured in production')
else:
    SECRET_KEY = 'dev-only-secret-key'

ALLOWED_HOSTS = _env_list('DJANGO_ALLOWED_HOSTS')
if not ALLOWED_HOSTS:
    if IS_PRODUCTION:
        raise ImproperlyConfigured('DJANGO_ALLOWED_HOSTS must be configured in production')
    ALLOWED_HOSTS = ['localhost', '127.0.0.1']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.broadcast',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'social_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'social_manager.wsgi.application'
ASGI_APPLICATION = 'social_manager.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / os.getenv('SQLITE_NAME', 'db.sqlite3'),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('TIME_ZONE', 'UTC')
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = _env_bool('DJANGO_SECURE_SSL_REDIRECT', default=True)
    SESSION_COOKIE_SECURE = _env_bool('DJANGO_SESSION_COOKIE_SECURE', default=True)
    CSRF_COOKIE_SECURE = _env_bool('DJANGO_CSRF_COOKIE_SECURE', default=True)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv('DJANGO_SESSION_COOKIE_SAMESITE', 'Lax')
    CSRF_COOKIE_SAMESITE = os.getenv('DJANGO_CSRF_COOKIE_SAMESITE', 'Lax')
    SECURE_HSTS_SECONDS = int(os.getenv('DJANGO_SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = _env_bool('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
    SECURE_HSTS_PRELOAD = _env_bool('DJANGO_SECURE_HSTS_PRELOAD', default=True)

# Context7 integration configuration
CONTEXT7_BASE_URL = os.getenv('CONTEXT7_BASE_URL', 'https://api.context7.com')
CONTEXT7_API_KEY = os.getenv('CONTEXT7_API_KEY', '')

# OpenAI integration configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_CHAT_MODEL = os.getenv('OPENAI_CHAT_MODEL', 'gpt-4o-mini')
OPENAI_IMAGE_MODEL = os.getenv('OPENAI_IMAGE_MODEL', 'gpt-image-1')
