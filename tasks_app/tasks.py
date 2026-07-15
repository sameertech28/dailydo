from celery import shared_task
from django.utils import timezone
import logging
from .utils import (
    is_quiet_hours, send_reminder_email, send_no_tasks_email,
    send_day_end_email, should_send_reminder, send_morning_email
)

logger = logging.getLogger(__name__)

@shared_task
def send_morning_tasks():
    """Send morning email at 7 AM to users with tasks scheduled for today."""
    from django.contrib.auth import get_user_model
    from .models import Task

    User = get_user_model()
    today = timezone.now().date()
    sent_count = 0

    for user in User.objects.filter(is_active=True):
        try:
            pending_tasks = Task.objects.filter(user=user, date=today, status='pending')
            if pending_tasks.exists():
                if send_morning_email(user, list(pending_tasks)):
                    sent_count += 1
        except Exception as e:
            logger.error(f'Error processing morning tasks for {user.email}: {e}')

    logger.info(f'Morning advance tasks complete: sent {sent_count} emails.')
    return {'status': 'done', 'sent': sent_count}


@shared_task
def send_reminders():
    """Send reminders to users with pending tasks."""
    from django.contrib.auth import get_user_model
    from .models import Task

    if is_quiet_hours():
        logger.info('Quiet hours — skipping reminders.')
        return {'status': 'quiet_hours', 'sent': 0}

    User = get_user_model()
    today = timezone.now().date()
    sent_count = 0

    for user in User.objects.filter(is_active=True):
        try:
            if not should_send_reminder(user):
                continue

            pending_tasks = Task.objects.filter(user=user, date=today, status='pending')

            if pending_tasks.exists():
                if send_reminder_email(user, list(pending_tasks)):
                    sent_count += 1
        except Exception as e:
            logger.error(f'Error processing reminders for {user.email}: {e}')

    logger.info(f'Reminder task complete: sent {sent_count} emails.')
    return {'status': 'done', 'sent': sent_count}


@shared_task
def check_no_tasks():
    """Remind users who haven't added any tasks today."""
    from django.contrib.auth import get_user_model
    from .models import Task

    if is_quiet_hours():
        return {'status': 'quiet_hours', 'sent': 0}

    User = get_user_model()
    today = timezone.now().date()
    sent_count = 0

    for user in User.objects.filter(is_active=True):
        try:
            if not should_send_reminder(user):
                continue

            has_tasks = Task.objects.filter(user=user, date=today).exists()
            if not has_tasks:
                if send_no_tasks_email(user):
                    sent_count += 1
        except Exception as e:
            logger.error(f'Error checking no-tasks for {user.email}: {e}')

    return {'status': 'done', 'sent': sent_count}


@shared_task
def auto_archive_tasks():
    """Archive all pending tasks at end of day and send summary emails."""
    from django.contrib.auth import get_user_model
    from .models import Task, DailyRecord

    User = get_user_model()
    today = timezone.now().date()
    processed = 0

    for user in User.objects.filter(is_active=True):
        try:
            pending_tasks = Task.objects.filter(user=user, date=today, status='pending')

            if not pending_tasks.exists() and not Task.objects.filter(user=user, date=today).exists():
                continue

            archived_list = list(pending_tasks)
            archived_count = pending_tasks.count()

            pending_tasks.update(status='archived', archived_date=today)

            completed = Task.objects.filter(user=user, date=today, status='completed').count()
            removed = Task.objects.filter(user=user, date=today, status='removed').count()
            all_tasks = Task.objects.filter(user=user, date=today)

            record, _ = DailyRecord.objects.get_or_create(user=user, date=today)
            record.total_tasks = all_tasks.count()
            record.completed_tasks = completed
            record.removed_tasks = removed
            record.archived_tasks = archived_count
            record.all_completed = (archived_count == 0 and completed > 0)
            record.save()

            send_day_end_email(user, completed, removed, archived_list, list(all_tasks))
            processed += 1
        except Exception as e:
            logger.error(f'Error archiving tasks for {user.email}: {e}')

    logger.info(f'Auto-archive complete: processed {processed} users.')
    return {'status': 'done', 'processed': processed}
