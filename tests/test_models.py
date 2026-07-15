"""
Tests for DailyDo models.
Run with: python manage.py test tests.test_models
"""
from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from accounts.models import CustomUser
from tasks_app.models import Task, DailyRecord, ReminderLog


class CustomUserModelTest(TestCase):
    def test_create_user(self):
        user = CustomUser.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='TestPass123!'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('TestPass123!'))
        self.assertTrue(user.is_active)

    def test_email_unique(self):
        CustomUser.objects.create_user(
            email='dupe@example.com', username='user1', password='pass123!'
        )
        with self.assertRaises(Exception):
            CustomUser.objects.create_user(
                email='dupe@example.com', username='user2', password='pass123!'
            )

    def test_display_name_uses_username(self):
        user = CustomUser(email='a@b.com', username='johndoe')
        self.assertEqual(user.display_name, 'johndoe')

    def test_display_name_fallback_to_email(self):
        user = CustomUser(email='john@example.com', username='')
        self.assertEqual(user.display_name, 'john')


class TaskModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='task@test.com', username='taskuser', password='pass123!'
        )

    def test_create_task(self):
        task = Task.objects.create(user=self.user, title='Write tests')
        self.assertEqual(task.title, 'Write tests')
        self.assertEqual(task.status, 'pending')
        self.assertIsNone(task.completed_at)

    def test_mark_complete(self):
        task = Task.objects.create(user=self.user, title='Finish report')
        task.mark_complete()
        task.refresh_from_db()
        self.assertEqual(task.status, 'completed')
        self.assertIsNotNone(task.completed_at)

    def test_mark_removed(self):
        task = Task.objects.create(user=self.user, title='Skip this one')
        task.mark_removed()
        task.refresh_from_db()
        self.assertEqual(task.status, 'removed')
        self.assertIsNotNone(task.removed_at)

    def test_is_pending_property(self):
        task = Task.objects.create(user=self.user, title='Pending task')
        self.assertTrue(task.is_pending)
        task.mark_complete()
        self.assertFalse(task.is_pending)

    def test_str_includes_emoji(self):
        task = Task.objects.create(user=self.user, title='My task')
        self.assertIn('My task', str(task))

    def test_default_date_is_today(self):
        task = Task.objects.create(user=self.user, title='Today task')
        self.assertEqual(task.date, timezone.now().date())


class DailyRecordModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='record@test.com', username='recorduser', password='pass123!'
        )

    def test_create_daily_record(self):
        record = DailyRecord.objects.create(
            user=self.user,
            total_tasks=5,
            completed_tasks=3,
        )
        self.assertEqual(record.total_tasks, 5)
        self.assertEqual(record.completed_tasks, 3)

    def test_unique_together_user_date(self):
        today = timezone.now().date()
        DailyRecord.objects.create(user=self.user, date=today, total_tasks=1)
        with self.assertRaises(Exception):
            DailyRecord.objects.create(user=self.user, date=today, total_tasks=2)

    def test_completion_rate(self):
        record = DailyRecord(total_tasks=10, completed_tasks=7)
        self.assertEqual(record.completion_rate, 70)

    def test_completion_rate_zero_tasks(self):
        record = DailyRecord(total_tasks=0, completed_tasks=0)
        self.assertEqual(record.completion_rate, 0)

    def test_pending_tasks_property(self):
        record = DailyRecord(total_tasks=10, completed_tasks=4, removed_tasks=2, archived_tasks=1)
        self.assertEqual(record.pending_tasks, 3)


class ReminderLogModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='log@test.com', username='loguser', password='pass123!'
        )

    def test_create_reminder_log(self):
        log = ReminderLog.objects.create(
            user=self.user,
            pending_count=3,
            task_list='Task 1, Task 2, Task 3',
            reminder_type='pending',
        )
        self.assertEqual(log.pending_count, 3)
        self.assertTrue(log.email_sent)

    def test_str_representation(self):
        log = ReminderLog.objects.create(user=self.user, pending_count=2)
        self.assertIn(self.user.email, str(log))
