from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import View, ListView
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count
from .models import Task, DailyRecord, ReminderLog
from .forms import TaskForm
from .utils import can_add_task, get_remaining_slots, MAX_TASKS_PER_DAY


class DashboardView(LoginRequiredMixin, View):
    template_name = 'tasks/dashboard.html'

    def get(self, request):
        today = timezone.now().date()
        tasks = Task.objects.filter(user=request.user, date=today).exclude(status='archived')

        pending = tasks.filter(status='pending')
        completed = tasks.filter(status='completed')
        removed = tasks.filter(status='removed')

        record, _ = DailyRecord.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={'total_tasks': tasks.count()}
        )
        record.total_tasks = tasks.count()
        record.completed_tasks = completed.count()
        record.removed_tasks = removed.count()
        record.save(update_fields=['total_tasks', 'completed_tasks', 'removed_tasks'])

        remaining_slots = get_remaining_slots(request.user)
        last_reminder = ReminderLog.objects.filter(user=request.user).first()

        context = {
            'tasks': tasks,
            'pending_tasks': pending,
            'completed_tasks': completed,
            'removed_tasks': removed,
            'pending_count': pending.count(),
            'completed_count': completed.count(),
            'removed_count': removed.count(),
            'total_count': tasks.count(),
            'remaining_slots': remaining_slots,
            'max_tasks': MAX_TASKS_PER_DAY,
            'can_add': can_add_task(request.user),
            'record': record,
            'last_reminder': last_reminder,
            'today': today,
            'completion_rate': record.completion_rate,
        }
        return render(request, self.template_name, context)


class AddTaskView(LoginRequiredMixin, View):
    template_name = 'tasks/add_task.html'

    def get(self, request):
        if not can_add_task(request.user):
            messages.error(request, f'You have reached the maximum limit of {MAX_TASKS_PER_DAY} tasks per day.')
            return redirect('dashboard')
        context = {
            'remaining_slots': get_remaining_slots(request.user),
            'max_tasks': MAX_TASKS_PER_DAY,
        }
        return render(request, self.template_name, context)

    def post(self, request):
        if not can_add_task(request.user):
            messages.error(request, f'Daily limit of {MAX_TASKS_PER_DAY} tasks reached.')
            return redirect('dashboard')

        titles = request.POST.getlist('title')
        descriptions = request.POST.getlist('description')
        date_str = request.POST.get('date', '').strip()
        
        from datetime import datetime
        if date_str:
            try:
                task_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                task_date = timezone.now().date()
        else:
            task_date = timezone.now().date()
            
        current_count = Task.objects.filter(user=request.user, date=task_date).exclude(status='archived').count()
        valid_titles = [t.strip() for t in titles if t.strip()]
        
        if current_count + len(valid_titles) > MAX_TASKS_PER_DAY:
            messages.error(request, f'Cannot add {len(valid_titles)} tasks. You only have {MAX_TASKS_PER_DAY - current_count} slots left for this date.')
            return redirect('add_task')
            
        if not valid_titles:
            messages.error(request, 'Please provide at least one task title.')
            return redirect('add_task')

        new_tasks = []
        for i, title in enumerate(titles):
            title = title.strip()
            if not title:
                continue
            desc = descriptions[i].strip() if i < len(descriptions) else ''
            
            task = Task.objects.create(
                user=request.user,
                title=title,
                description=desc,
                date=task_date
            )
            new_tasks.append(task)

        record, _ = DailyRecord.objects.get_or_create(user=request.user, date=task_date)
        record.total_tasks = Task.objects.filter(
            user=request.user, date=task_date
        ).exclude(status='archived').count()
        record.save(update_fields=['total_tasks'])
        
        # Send instant email confirmation for today's tasks
        today = timezone.now().date()
        if new_tasks and task_date == today:
            from .utils import send_tasks_confirmed_email
            pending = Task.objects.filter(user=request.user, date=today, status='pending')
            send_tasks_confirmed_email(request.user, list(pending))

        messages.success(request, f'{len(valid_titles)} task{"s" if len(valid_titles) != 1 else ""} added successfully! Confirmation email sent.')
        return redirect('dashboard')


class EditTaskView(LoginRequiredMixin, View):
    template_name = 'tasks/edit_task.html'

    def get(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        if task.status != 'pending':
            messages.warning(request, 'Only pending tasks can be edited.')
            return redirect('dashboard')
        form = TaskForm(instance=task)
        return render(request, self.template_name, {'form': form, 'task': task})

    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        if task.status != 'pending':
            messages.warning(request, 'Only pending tasks can be edited.')
            return redirect('dashboard')
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully.')
            return redirect('dashboard')
        return render(request, self.template_name, {'form': form, 'task': task})


class CompleteTaskView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        if task.status == 'pending':
            task.mark_complete()
            messages.success(request, f'"{task.title}" marked as complete! 🎉')
        else:
            messages.warning(request, 'This task cannot be completed.')
        return redirect('dashboard')


class RemoveTaskView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        if task.status == 'pending':
            task.mark_removed()
            messages.info(request, f'"{task.title}" skipped for today.')
        else:
            messages.warning(request, 'This task cannot be skipped.')
        return redirect('dashboard')


class DeleteTaskView(LoginRequiredMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        title = task.title
        date = task.date
        task.delete()
        
        # Recalculate total_tasks for the day
        record = DailyRecord.objects.filter(user=request.user, date=date).first()
        if record:
            total = Task.objects.filter(user=request.user, date=date).exclude(status='archived').count()
            record.total_tasks = total
            record.save(update_fields=['total_tasks'])
            
        messages.info(request, f'"{title}" permanently deleted.')
        return redirect('dashboard')


class ArchiveView(LoginRequiredMixin, View):
    template_name = 'tasks/archive.html'

    def get(self, request):
        date_filter = request.GET.get('date', '')
        tasks = Task.objects.filter(user=request.user, status='archived').order_by('-archived_date', '-created_at')

        if date_filter:
            from datetime import datetime
            try:
                filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
                tasks = tasks.filter(archived_date=filter_date)
            except ValueError:
                pass

        archive_dates = Task.objects.filter(
            user=request.user, status='archived'
        ).values_list('archived_date', flat=True).distinct().order_by('-archived_date')

        context = {
            'tasks': tasks,
            'date_filter': date_filter,
            'archive_dates': archive_dates,
            'total_archived': tasks.count(),
        }
        return render(request, self.template_name, context)


class HistoryView(LoginRequiredMixin, View):
    template_name = 'tasks/history.html'

    def get(self, request):
        records = DailyRecord.objects.filter(user=request.user).order_by('-date')[:30]
        # Attach tasks to each record for preview
        for record in records:
            day_tasks = Task.objects.filter(user=request.user, date=record.date)
            record.completed_list = day_tasks.filter(status='completed')[:3]
            record.skipped_list = day_tasks.filter(status='removed')[:3]
            record.completed_total = day_tasks.filter(status='completed').count()
            record.skipped_total = day_tasks.filter(status='removed').count()
        context = {'records': records}
        return render(request, self.template_name, context)


class HistoryDetailView(LoginRequiredMixin, View):
    template_name = 'tasks/history_detail.html'

    def get(self, request, date_str):
        from datetime import datetime
        try:
            day = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format.')
            return redirect('history')

        record = DailyRecord.objects.filter(user=request.user, date=day).first()
        all_tasks = Task.objects.filter(user=request.user, date=day)
        completed = all_tasks.filter(status='completed')
        skipped = all_tasks.filter(status='removed')
        archived = all_tasks.filter(status='archived')
        pending = all_tasks.filter(status='pending')

        context = {
            'day': day,
            'record': record,
            'completed_tasks': completed,
            'skipped_tasks': skipped,
            'archived_tasks': archived,
            'pending_tasks': pending,
            'completed_count': completed.count(),
            'skipped_count': skipped.count(),
            'archived_count': archived.count(),
            'pending_count': pending.count(),
            'total_count': all_tasks.count(),
            'completion_rate': record.completion_rate if record else 0,
        }
        return render(request, self.template_name, context)


class TriggerReminderView(LoginRequiredMixin, View):
    """Dev/test view to manually trigger a reminder email."""
    def post(self, request):
        from .utils import send_reminder_email, send_no_tasks_email
        today = timezone.now().date()
        pending = Task.objects.filter(user=request.user, date=today, status='pending')
        if pending.exists():
            send_reminder_email(request.user, list(pending))
            messages.success(request, f'Reminder email sent with {pending.count()} pending tasks.')
        else:
            send_no_tasks_email(request.user)
            messages.info(request, 'No-tasks email sent to your inbox.')
        return redirect('dashboard')


class ConfirmTasksView(LoginRequiredMixin, View):
    def post(self, request):
        from .utils import send_tasks_confirmed_email
        today = timezone.now().date()
        pending = Task.objects.filter(user=request.user, date=today, status='pending')
        if pending.exists():
            send_tasks_confirmed_email(request.user, list(pending))
            messages.success(request, f'Confirmation email sent with your {pending.count()} tasks for today.')
        else:
            messages.info(request, 'No pending tasks to confirm for today.')
        return redirect('dashboard')


class UpcomingTasksView(LoginRequiredMixin, View):
    template_name = 'tasks/upcoming.html'

    def get(self, request):
        today = timezone.now().date()
        tasks = Task.objects.filter(user=request.user, date__gt=today).exclude(status='archived').order_by('date')
        context = {
            'tasks': tasks,
            'total_count': tasks.count(),
        }
        return render(request, self.template_name, context)

import csv
from django.http import HttpResponse

class ExportTasksCSVView(LoginRequiredMixin, View):
    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="tasks_history.csv"'

        writer = csv.writer(response)
        writer.writerow(['Date', 'Title', 'Description', 'Status', 'Created At'])

        tasks = Task.objects.filter(user=request.user).order_by('-date')
        for task in tasks:
            writer.writerow([
                task.date,
                task.title,
                task.description,
                task.status,
                task.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        return response
