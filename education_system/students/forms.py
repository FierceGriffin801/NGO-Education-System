from django import forms
from .models import Student, Attendance, Grade
from centers.models import Center
from datetime import date

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ['student_id', 'first_name', 'last_name', 'date_of_birth', 
                 'gender', 'center', 'guardian_name', 'guardian_phone']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'student_id': forms.TextInput(attrs={'placeholder': 'Enter unique student ID'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
            'guardian_name': forms.TextInput(attrs={'placeholder': 'Guardian Full Name'}),
            'guardian_phone': forms.TextInput(attrs={'placeholder': '+91 XXXXXXXXXX'}),
        }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'is_present', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'remarks': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional remarks'}),
        }

class GradeForm(forms.ModelForm):
    class Meta:
        model = Grade
        fields = ['student', 'subject', 'assessment_date', 'marks_obtained', 'total_marks', 'grade_letter']
        widgets = {
            'assessment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'marks_obtained': forms.NumberInput(attrs={'min': 0, 'class': 'form-control'}),
            'total_marks': forms.NumberInput(attrs={'min': 1, 'class': 'form-control'}),
            'grade_letter': forms.TextInput(attrs={'class': 'form-control'}),
        }


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'is_present', 'remarks']
        widgets = {
            'date': forms.DateInput(attrs={
                'type': 'date', 
                'class': 'form-control',
                'value': date.today().strftime('%Y-%m-%d')
            }),
            'remarks': forms.Textarea(attrs={
                'rows': 2, 
                'placeholder': 'Optional remarks...',
                'class': 'form-control'
            }),
        }

class BulkAttendanceForm(forms.Form):
    attendance_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control',
            'value': date.today().strftime('%Y-%m-%d')
        }),
        initial=date.today
    )
    center = forms.ModelChoiceField(
        queryset=Center.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        empty_label="Select Center"
    )