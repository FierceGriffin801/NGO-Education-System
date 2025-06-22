from django.db import models
from django.contrib.auth.models import User
from students.models import Student
from centers.models import Center

class Report(models.Model):
    REPORT_TYPES = [
        ('attendance', 'Attendance Report'),
        ('academic', 'Academic Performance Report'),
        ('center', 'Center Performance Report'),
        ('financial', 'Financial Report'),
        ('donor', 'Donor Impact Report'),
        ('risk', 'Risk Assessment Report'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    date_from = models.DateField()
    date_to = models.DateField()
    centers = models.ManyToManyField(Center, blank=True)
    file_path = models.FileField(upload_to='reports/', blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_report_type_display()}"

class ReportSchedule(models.Model):
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=Report.REPORT_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    recipients = models.TextField(help_text="Email addresses separated by commas")
    centers = models.ManyToManyField(Center, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    last_run = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_frequency_display()}"
