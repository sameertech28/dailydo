"""
Tests for DailyDo views.
Run with: python manage.py test tests.test_views
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import CustomUser
from tasks_app.models import Task, DailyRecord


class AuthViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='view@test.com', username='viewuser', password='TestPass123!'
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign in')

    def test_register_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create')

    def test_login_with_valid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'view@test.com',
            'password': 'TestPass123!',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_with_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'view@test.com',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)

    def test_register_new_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(CustomUser.objects.filter(email='new@test.com').exists())

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, '/accounts/login/?next=/')

    def test_logout(self):
        self.client.login(username='view@test.com', password='TestPass123!')
        response = self.client.post(reverse('logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)


class TaskViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            email='task@test.com', username='taskview', password='TestPass123!'
        )
        self.client.login(username='task@test.com', password='TestPass123!')

    def test_dashboard_loads(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Today')

    def test_add_task_page_loads(self):
        response = self.client.get(reverse('add_task'))
        self.assertEqual(response.status_code, 200)

    def test_add_task_valid_data(self):
        response = self.client.post(reverse('add_task'), {
            'title': 'My test task',
            'description': 'Some description',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Task.objects.filter(user=self.user, title='My test task').exists())

    def test_add_task_empty_title(self):
        response = self.client.post(reverse('add_task'), {
            'title': '',
            'description': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Task.objects.filter(user=self.user, title='').exists())

    def test_complete_task(self):
        task = Task.objects.create(user=self.user, title='Complete me')
        response = self.client.post(
            reverse('complete_task', kwargs={'pk': task.pk}), follow=True
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')

    def test_remove_task(self):
        task = Task.objects.create(user=self.user, title='Remove me')
        response = self.client.post(
            reverse('remove_task', kwargs={'pk': task.pk}), follow=True
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.status, 'removed')

    def test_edit_task_page_loads(self):
        task = Task.objects.create(user=self.user, title='Edit me')
        response = self.client.get(reverse('edit_task', kwargs={'pk': task.pk}))
        self.assertEqual(response.status_code, 200)

    def test_edit_task_valid_data(self):
        task = Task.objects.create(user=self.user, title='Old title')
        response = self.client.post(
            reverse('edit_task', kwargs={'pk': task.pk}),
            {'title': 'New title', 'description': ''},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        self.assertEqual(task.title, 'New title')

    def test_cannot_edit_completed_task(self):
        task = Task.objects.create(user=self.user, title='Done task', status='completed')
        response = self.client.get(
            reverse('edit_task', kwargs={'pk': task.pk}), follow=True
        )
        self.assertRedirects(response, reverse('dashboard'))

    def test_archive_page_loads(self):
        response = self.client.get(reverse('archive'))
        self.assertEqual(response.status_code, 200)

    def test_history_page_loads(self):
        response = self.client.get(reverse('history'))
        self.assertEqual(response.status_code, 200)

    def test_profile_page_loads(self):
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)

    def test_cannot_access_other_users_task(self):
        other_user = CustomUser.objects.create_user(
            email='other@test.com', username='otheruser', password='TestPass123!'
        )
        task = Task.objects.create(user=other_user, title='Not your task')
        response = self.client.post(
            reverse('complete_task', kwargs={'pk': task.pk}), follow=True
        )
        self.assertEqual(response.status_code, 404)

    def test_task_limit_50(self):
        today = timezone.now().date()
        for i in range(50):
            Task.objects.create(user=self.user, title=f'Task {i}', date=today)

        response = self.client.get(reverse('add_task'), follow=True)
        self.assertRedirects(response, reverse('dashboard'))
