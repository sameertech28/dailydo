from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

MAX_TASKS_PER_DAY = 50
QUIET_HOUR_START = 23  # 11 PM
QUIET_HOUR_END = 5     # 5 AM


def is_quiet_hours():
    """Check if current time is within quiet hours (11 PM - 5 AM)."""
    now = timezone.localtime(timezone.now())
    hour = now.hour
    return hour >= QUIET_HOUR_START or hour < QUIET_HOUR_END


def get_today_task_count(user):
    """Get total tasks for today (all statuses except archived)."""
    from .models import Task
    today = timezone.now().date()
    return Task.objects.filter(user=user, date=today).exclude(status='archived').count()


def can_add_task(user):
    """Check if user can add more tasks today."""
    return get_today_task_count(user) < MAX_TASKS_PER_DAY


def get_remaining_slots(user):
    """Get number of remaining task slots."""
    return MAX_TASKS_PER_DAY - get_today_task_count(user)


def send_reminder_email(user, pending_tasks):
    """Send reminder email with pending tasks list."""
    try:
        pending_count = len(pending_tasks)
        task_names = [t.title for t in pending_tasks]

        context = {
            'user': user,
            'pending_count': pending_count,
            'pending_tasks': pending_tasks,
            'site_url': settings.SITE_URL,
        }

        subject = f'Reminder - {pending_count} task{"s" if pending_count != 1 else ""} pending for today'
        html_content = render_to_string('emails/reminder.html', context)
        text_content = render_to_string('emails/reminder.txt', context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[settings.EMAIL_HOST_USER],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        from .models import ReminderLog
        ReminderLog.objects.create(
            user=user,
            pending_count=pending_count,
            task_list=', '.join(task_names),
            email_sent=True,
            reminder_type='pending',
        )
        logger.info(f'Reminder email sent to {user.email} ({pending_count} tasks)')
        return True
    except Exception as e:
        logger.error(f'Failed to send reminder to {user.email}: {e}')
        return False


def send_no_tasks_email(user):
    """Send email when user has added no tasks today."""
    try:
        context = {
            'user': user,
            'site_url': settings.SITE_URL,
        }
        subject = 'DailyDo - Add your tasks for today'
        html_content = render_to_string('emails/no_tasks.html', context)
        text_content = render_to_string('emails/no_tasks.txt', context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[settings.EMAIL_HOST_USER],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        from .models import ReminderLog
        ReminderLog.objects.create(
            user=user,
            pending_count=0,
            task_list='',
            email_sent=True,
            reminder_type='no_tasks',
        )
        logger.info(f'No-tasks email sent to {user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send no-tasks email to {user.email}: {e}')
        return False


def send_day_end_email(user, completed, removed, archived, all_tasks):
    """Send day-end summary email."""
    try:
        today = timezone.now().date()
        context = {
            'user': user,
            'date': today,
            'completed': completed,
            'removed': removed,
            'archived': archived,
            'all_tasks': all_tasks,
            'site_url': settings.SITE_URL,
        }
        subject = f'Day Complete - {today.strftime("%B %d, %Y")} Summary'
        html_content = render_to_string('emails/day_end.html', context)
        text_content = render_to_string('emails/day_end.txt', context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[settings.EMAIL_HOST_USER],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        from .models import ReminderLog
        ReminderLog.objects.create(
            user=user,
            pending_count=0,
            task_list='',
            email_sent=True,
            reminder_type='day_end',
        )
        logger.info(f'Day-end summary sent to {user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send day-end email to {user.email}: {e}')
        return False


def send_tasks_confirmed_email(user, pending_tasks):
    """Send immediate email confirming tasks added for today."""
    try:
        task_count = len(pending_tasks)
        task_names = [t.title for t in pending_tasks]
        context = {
            'user': user,
            'task_count': task_count,
            'pending_tasks': pending_tasks,
            'site_url': settings.SITE_URL,
        }
        subject = f'Tasks Confirmed - {task_count} task{"s" if task_count != 1 else ""} on your plate today'
        html_content = render_to_string('emails/confirmed_tasks.html', context)
        text_content = render_to_string('emails/confirmed_tasks.txt', context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[settings.EMAIL_HOST_USER],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        from .models import ReminderLog
        ReminderLog.objects.create(
            user=user,
            pending_count=task_count,
            task_list=', '.join(task_names),
            email_sent=True,
            reminder_type='pending',
        )
        logger.info(f'Task confirmation email sent to {user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send confirmation email to {user.email}: {e}')
        return False


def send_morning_email(user, tasks):
    """Send morning email with the tasks scheduled for today."""
    try:
        task_count = len(tasks)
        context = {
            'user': user,
            'task_count': task_count,
            'tasks': tasks,
            'site_url': settings.SITE_URL,
        }
        subject = f'Good Morning - You have {task_count} task{"s" if task_count != 1 else ""} scheduled for today'
        html_content = render_to_string('emails/morning_tasks.html', context)
        text_content = render_to_string('emails/morning_tasks.txt', context)

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
            reply_to=[settings.EMAIL_HOST_USER],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()

        from .models import ReminderLog
        ReminderLog.objects.create(
            user=user,
            pending_count=task_count,
            task_list=', '.join([t.title for t in tasks]),
            email_sent=True,
            reminder_type='pending',
        )
        logger.info(f'Morning advance tasks email sent to {user.email}')
        return True
    except Exception as e:
        logger.error(f'Failed to send morning email to {user.email}: {e}')
        return False



def should_send_reminder(user):
    """Determine if reminder should be sent based on last reminder time."""
    from .models import ReminderLog
    from datetime import timedelta

    last_reminder = ReminderLog.objects.filter(
        user=user, email_sent=True, reminder_type__in=['pending', 'no_tasks']
    ).first()

    if not last_reminder:
        return True

    hours_since = (timezone.now() - last_reminder.sent_at).total_seconds() / 3600
    return hours_since >= 4
