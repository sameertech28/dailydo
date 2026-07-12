from django.db import models
from django.conf import settings
from django.utils import timezone

STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('completed', 'Completed'),
    ('removed', 'Removed'),
    ('archived', 'Archived'),
]

STATUS_EMOJI = {
    'pending': '⏳',
    'completed': '✅',
    'removed': '🗑️',
    'archived': '📦',
}


class Task(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    removed_at = models.DateTimeField(null=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    archived_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        emoji = STATUS_EMOJI.get(self.status, '⏳')
        return f"{emoji} {self.title}"

    def mark_complete(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'completed_at'])
        self._update_daily_record()

    def mark_removed(self):
        self.status = 'removed'
        self.removed_at = timezone.now()
        self.save(update_fields=['status', 'removed_at'])
        self._update_daily_record()

    def _update_daily_record(self):
        record, _ = DailyRecord.objects.get_or_create(user=self.user, date=self.date)
        pending = Task.objects.filter(user=self.user, date=self.date, status='pending').count()
        completed = Task.objects.filter(user=self.user, date=self.date, status='completed').count()
        removed = Task.objects.filter(user=self.user, date=self.date, status='removed').count()
        record.completed_tasks = completed
        record.removed_tasks = removed
        record.all_completed = (pending == 0 and (completed + removed) > 0)
        record.save(update_fields=['completed_tasks', 'removed_tasks', 'all_completed'])

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_completed(self):
        return self.status == 'completed'

    @property
    def status_badge_class(self):
        classes = {
            'pending': 'badge-pending',
            'completed': 'badge-completed',
            'removed': 'badge-removed',
            'archived': 'badge-archived',
        }
        return classes.get(self.status, 'badge-pending')


class DailyRecord(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='daily_records')
    date = models.DateField(default=timezone.localdate)
    total_tasks = models.IntegerField(default=0)
    completed_tasks = models.IntegerField(default=0)
    removed_tasks = models.IntegerField(default=0)
    archived_tasks = models.IntegerField(default=0)
    all_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.email} - {self.date}"

    @property
    def pending_tasks(self):
        return self.total_tasks - self.completed_tasks - self.removed_tasks - self.archived_tasks

    @property
    def completion_rate(self):
        if self.total_tasks == 0:
            return 0
        return round((self.completed_tasks / self.total_tasks) * 100)


class ReminderLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reminder_logs')
    sent_at = models.DateTimeField(auto_now_add=True)
    pending_count = models.IntegerField(default=0)
    task_list = models.TextField(blank=True, default='')
    email_sent = models.BooleanField(default=True)
    reminder_type = models.CharField(max_length=50, default='pending', choices=[
        ('pending', 'Pending Tasks'),
        ('no_tasks', 'No Tasks Added'),
        ('day_end', 'Day End Summary'),
    ])

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Reminder to {self.user.email} at {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
