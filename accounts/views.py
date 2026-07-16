from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import CreateView, FormView, View, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import RegisterForm, LoginForm, SettingsForm
from tasks_app.models import DailyRecord, Task
from django.utils import timezone


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        messages.success(self.request, f'Account created! Welcome aboard, {user.display_name}! Please log in.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please fix the errors below.')
        return super().form_invalid(form)


class LoginView(FormView):
    form_class = LoginForm
    template_name = 'accounts/login.html'
    success_url = reverse_lazy('dashboard')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        messages.success(self.request, f'Welcome back, {user.display_name}! 👋')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid email or password. Please try again.')
        return super().form_invalid(form)


class LogoutView(View):
    def post(self, request):
        logout(request)
        messages.info(request, 'You have been logged out. See you tomorrow! 👋')
        return redirect('login')


class ProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        today = timezone.now().date()
        total_records = DailyRecord.objects.filter(user=request.user).count()
        total_tasks_ever = Task.objects.filter(user=request.user).count()
        completed_ever = Task.objects.filter(user=request.user, status='completed').count()
        streak = self._get_streak(request.user)
        context = {
            'total_records': total_records,
            'total_tasks_ever': total_tasks_ever,
            'completed_ever': completed_ever,
            'streak': streak,
            'completion_rate': round((completed_ever / total_tasks_ever * 100) if total_tasks_ever > 0 else 0),
        }
        return render(request, self.template_name, context)

    def _get_streak(self, user):
        from datetime import timedelta
        records = DailyRecord.objects.filter(user=user).order_by('-date')
        if not records.exists():
            return 0
        streak = 0
        check_date = timezone.now().date()
        for record in records:
            if record.date == check_date and record.completed_tasks > 0:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break
        return streak


class SettingsView(LoginRequiredMixin, UpdateView):
    template_name = 'accounts/settings.html'
    form_class = SettingsForm
    success_url = reverse_lazy('profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Your profile settings have been updated successfully.')
        return super().form_valid(form)
