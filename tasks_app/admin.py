from django.contrib import admin
from .models import Task, DailyRecord, ReminderLog


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'date', 'created_at')
    list_filter = ('status', 'date')
    search_fields = ('title', 'user__email')
    ordering = ('-created_at',)


@admin.register(DailyRecord)
class DailyRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'total_tasks', 'completed_tasks', 'removed_tasks', 'archived_tasks', 'all_completed')
    list_filter = ('date', 'all_completed')
    ordering = ('-date',)


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'reminder_type', 'pending_count', 'email_sent', 'sent_at')
    list_filter = ('reminder_type', 'email_sent')
    ordering = ('-sent_at',)
