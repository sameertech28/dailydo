from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'What do you need to do today?',
            'class': 'form-control form-control-lg',
            'autofocus': True,
        }),
        help_text='Be specific — "Send project report to team" beats "work stuff".'
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Add notes, links, or context... (optional)',
            'class': 'form-control',
            'rows': 3,
        }),
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
        }),
        help_text='Leave empty to schedule for today.'
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'date']

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError('Task title cannot be empty.')
        return title
