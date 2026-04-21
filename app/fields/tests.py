from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile, Field
from datetime import date


class AuthTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='testadmin',
            password='testpass123'
        )
        UserProfile.objects.create(user=self.admin, role='admin')

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)

    def test_signup_page_loads(self):
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 200)

    def test_login_redirects_to_dashboard(self):
        response = self.client.post(reverse('login'), {
            'username': 'testadmin',
            'password': 'testpass123'
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/login/?next=/dashboard/')


class FieldTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_user(
            username='adminuser',
            password='adminpass123'
        )
        UserProfile.objects.create(user=self.admin, role='admin')
        self.client.login(username='adminuser', password='adminpass123')

        self.field = Field.objects.create(
            name='Test Field',
            crop_type='maize',
            planting_date=date.today(),
            current_stage='planted',
            created_by=self.admin,
        )

    def test_field_list_loads(self):
        response = self.client.get(reverse('field_list'))
        self.assertEqual(response.status_code, 200)

    def test_field_detail_loads(self):
        response = self.client.get(reverse('field_detail', args=[self.field.pk]))
        self.assertEqual(response.status_code, 200)

    def test_field_computed_status(self):
        self.assertIn(self.field.computed_status, ['active', 'at_risk', 'completed'])

    def test_field_str(self):
        self.assertEqual(str(self.field), 'Test Field — maize')