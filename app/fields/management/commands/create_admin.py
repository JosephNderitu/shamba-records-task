from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from fields.models import UserProfile


class Command(BaseCommand):
    help = 'Creates the default admin superuser if not exists'

    def handle(self, *args, **kwargs):
        username = 'Admin'
        email    = 'test.admin@gmail.com'
        password = 'Admin@2026'

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Admin user "{username}" already exists — skipping.'))
            return

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        UserProfile.objects.get_or_create(user=user, defaults={'role': 'admin'})
        self.stdout.write(self.style.SUCCESS(f'✅ Superuser "{username}" created successfully!'))