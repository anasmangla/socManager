import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('broadcast', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=80, unique=True)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('description', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.CreateModel(
            name='SocialAPICredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                (
                    'platform',
                    models.CharField(
                        choices=[
                            ('x', 'X / Twitter'),
                            ('facebook', 'Facebook'),
                            ('instagram', 'Instagram'),
                            ('linkedin', 'LinkedIn'),
                            ('tiktok', 'TikTok'),
                        ],
                        max_length=20,
                    ),
                ),
                ('app_name', models.CharField(max_length=120)),
                ('client_id', models.CharField(max_length=255)),
                ('client_secret', models.TextField(help_text='Store securely in production (vault/secret manager).')),
                ('access_token', models.TextField(blank=True)),
                ('refresh_token', models.TextField(blank=True)),
                ('api_base_url', models.URLField(blank=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['platform', 'app_name'],
                'unique_together': {('platform', 'app_name')},
            },
        ),
        migrations.CreateModel(
            name='BusinessCredential',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=120)),
                ('username', models.CharField(blank=True, max_length=255)),
                ('secret', models.TextField(help_text='Store securely in production (vault/secret manager).')),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                (
                    'business',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='credentials',
                        to='broadcast.businessaccount',
                    ),
                ),
            ],
            options={
                'ordering': ['business__name', 'label'],
                'unique_together': {('business', 'label')},
            },
        ),
    ]
