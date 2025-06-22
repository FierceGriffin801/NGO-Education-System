from django import forms
from .models import Report, ReportSchedule
from centers.models import Center
from datetime import date, timedelta

class ReportGenerationForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'report_type', 'date_from', 'date_to', 'centers']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter report title...'
            }),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
            'date_from': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
            }),
            'date_to': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'value': date.today().strftime('%Y-%m-%d')
            }),
            'centers': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

class ReportScheduleForm(forms.ModelForm):
    class Meta:
        model = ReportSchedule
        fields = ['name', 'report_type', 'frequency', 'recipients', 'centers']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Schedule name...'
            }),
            'report_type': forms.Select(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
            'recipients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter email addresses separated by commas...'
            }),
            'centers': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }
