"""
Tests for Celery tasks and business logic.
Run with: python manage.py test tests.test_tasks
"""
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch, MagicMock
from accounts.models import CustomUser
from tasks_app.models import Task, DailyRecord, ReminderLog
from tasks_app.utils import (
    is_quiet_hours, can_add_task, get_remaining_slots,
    should_send_reminder, MAX_TASKS_PER_DAY
)


class QuietHoursTest(TestCase):
    @patch('tasks_app.utils.timezone')
    def test_quiet_during_night(self, mock_tz):
        mock_now = MagicMock()
        mock_now.hour = 23  # 11 PM
        mock_tz.localtime.return_value = mock_now
        mock_tz.now.return_value = mock_now
        self.assertTrue(is_quiet_hours())

    @patch('tasks_app.utils.timezone')
    def test_quiet_during_early_morning(self, mock_tz):
        mock_now = MagicMock()
        mock_now.hour = 3  # 3 AM
        mock_tz.localtime.return_value = mock_now
        mock_tz.now.return_value = mock_now
        self.assertTrue(is_quiet_hours())

    @patch('tasks_app.utils.timezone')
    def test_not_quiet_during_day(self, mock_tz):
        mock_now = MagicMock()
        mock_now.hour = 10  # 10 AM
        mock_tz.localtime.return_value = mock_now
        mock_tz.now.return_value = mock_now
        self.assertFalse(is_quiet_hours())

    @patch('tasks_app.utils.timezone')
    def test_not_quiet_at_evening(self, mock_tz):
        mock_now = MagicMock()
        mock_now.hour = 20  # 8 PM
        mock_tz.localtime.return_value = mock_now
        mock_tz.now.return_value = mock_now
        self.assertFalse(is_quiet_hours())


class TaskLimitTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='limit@test.com', username='limituser', password='pass!'
        )

    def test_can_add_when_under_limit(self):
        self.assertTrue(can_add_task(self.user))

    def test_cannot_add_when_at_limit(self):
        today = timezone.now().date()
        for i in range(MAX_TASKS_PER_DAY):
            Task.objects.create(user=self.user, title=f'Task {i}', date=today)
        self.assertFalse(can_add_task(self.user))

    def test_remaining_slots(self):
        today = timezone.now().date()
        Task.objects.create(user=self.user, title='Task 1', date=today)
        Task.objects.create(user=self.user, title='Task 2', date=today)
        self.assertEqual(get_remaining_slots(self.user), MAX_TASKS_PER_DAY - 2)


class ShouldSendReminderTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='remind@test.com', username='reminduser', password='pass!'
        )

    def test_should_send_if_no_previous_reminder(self):
        self.assertTrue(should_send_reminder(self.user))

    def test_should_not_send_if_recent_reminder(self):
        ReminderLog.objects.create(
            user=self.user,
            pending_count=1,
            email_sent=True,
            reminder_type='pending',
        )
        self.assertFalse(should_send_reminder(self.user))

    def test_should_send_after_4_hours(self):
        from datetime import timedelta
        old_log = ReminderLog.objects.create(
            user=self.user,
            pending_count=1,
            email_sent=True,
            reminder_type='pending',
        )
        # Manually set sent_at to 5 hours ago
        ReminderLog.objects.filter(pk=old_log.pk).update(
            sent_at=timezone.now() - timedelta(hours=5)
        )
        self.assertTrue(should_send_reminder(self.user))


class CeleryTaskTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='celery@test.com', username='celeryuser', password='pass!'
        )

    @patch('tasks_app.tasks.is_quiet_hours', return_value=True)
    def test_send_reminders_skips_during_quiet_hours(self, mock_quiet):
        from tasks_app.tasks import send_reminders
        result = send_reminders()
        self.assertEqual(result['status'], 'quiet_hours')
        self.assertEqual(result['sent'], 0)

    @patch('tasks_app.tasks.is_quiet_hours', return_value=True)
    def test_check_no_tasks_skips_quiet_hours(self, mock_quiet):
        from tasks_app.tasks import check_no_tasks
        result = check_no_tasks()
        self.assertEqual(result['status'], 'quiet_hours')

    @patch('tasks_app.tasks.send_reminder_email', return_value=True)
    @patch('tasks_app.tasks.is_quiet_hours', return_value=False)
    def test_send_reminders_sends_for_pending_tasks(self, mock_quiet, mock_email):
        today = timezone.now().date()
        Task.objects.create(user=self.user, title='Pending', date=today, status='pending')
        from tasks_app.tasks import send_reminders
        result = send_reminders()
        self.assertEqual(result['status'], 'done')
        self.assertGreaterEqual(result['sent'], 1)

    @patch('tasks_app.utils.send_day_end_email', return_value=True)
    def test_auto_archive_archives_pending_tasks(self, mock_email):
        today = timezone.now().date()
        task = Task.objects.create(user=self.user, title='Archive me', date=today, status='pending')
        from tasks_app.tasks import auto_archive_tasks
        auto_archive_tasks()
        task.refresh_from_db()
        self.assertEqual(task.status, 'archived')
        self.assertEqual(task.archived_date, today)
