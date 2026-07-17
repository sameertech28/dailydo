from django.urls import path
from . import views

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('add/', views.AddTaskView.as_view(), name='add_task'),
    path('edit/<int:pk>/', views.EditTaskView.as_view(), name='edit_task'),
    path('complete/<int:pk>/', views.CompleteTaskView.as_view(), name='complete_task'),
    path('remove/<int:pk>/', views.RemoveTaskView.as_view(), name='remove_task'),
    path('delete/<int:pk>/', views.DeleteTaskView.as_view(), name='delete_task'),
    path('archive/', views.ArchiveView.as_view(), name='archive'),
    path('history/', views.HistoryView.as_view(), name='history'),
    path('history/<str:date_str>/', views.HistoryDetailView.as_view(), name='history_detail'),
    path('trigger-reminder/', views.TriggerReminderView.as_view(), name='trigger_reminder'),
    path('confirm-tasks/', views.ConfirmTasksView.as_view(), name='confirm_tasks'),
    path('upcoming/', views.UpcomingTasksView.as_view(), name='upcoming'),
    path('export/', views.ExportTasksCSVView.as_view(), name='export_tasks'),
]
