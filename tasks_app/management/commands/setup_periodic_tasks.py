from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, CrontabSchedule

class Command(BaseCommand):
    help = 'Setup celery beat periodic tasks'

    def handle(self, *args, **kwargs):
        # 1. Reminders every 4 hours during active hours
        schedule_reminders, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='5,9,13,17,21',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )
        PeriodicTask.objects.update_or_create(
            name='Send task reminders every 4 hours',
            defaults={
                'crontab': schedule_reminders,
                'task': 'tasks_app.tasks.send_reminders',
            }
        )

        # 2. No-task reminders every 4 hours during active hours
        schedule_no_tasks, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='6,10,14,18,20',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )
        PeriodicTask.objects.update_or_create(
            name='Send no-tasks reminder every 4 hours',
            defaults={
                'crontab': schedule_no_tasks,
                'task': 'tasks_app.tasks.check_no_tasks',
            }
        )

        # 3. Auto-archive at 11:59 PM
        schedule_archive, _ = CrontabSchedule.objects.get_or_create(
            minute='59',
            hour='23',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )
        PeriodicTask.objects.update_or_create(
            name='Auto-archive tasks at midnight',
            defaults={
                'crontab': schedule_archive,
                'task': 'tasks_app.tasks.auto_archive_tasks',
            }
        )

        # 4. Morning advance tasks email at 7:00 AM
        schedule_morning, _ = CrontabSchedule.objects.get_or_create(
            minute='0',
            hour='7',
            day_of_week='*',
            day_of_month='*',
            month_of_year='*'
        )
        PeriodicTask.objects.update_or_create(
            name='Send morning advance tasks email',
            defaults={
                'crontab': schedule_morning,
                'task': 'tasks_app.tasks.send_morning_tasks',
            }
        )

        self.stdout.write(self.style.SUCCESS('Successfully configured periodic tasks!'))
