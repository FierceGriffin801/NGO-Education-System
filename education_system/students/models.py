from django.db import models
from centers.models import Center, Subject

class Student(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    center = models.ForeignKey(Center, on_delete=models.CASCADE)
    enrollment_date = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    guardian_name = models.CharField(max_length=200)
    guardian_phone = models.CharField(max_length=15)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField()
    is_present = models.BooleanField()
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['student', 'date']

class Grade(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    assessment_date = models.DateField()
    marks_obtained = models.IntegerField()
    total_marks = models.IntegerField()
    grade_letter = models.CharField(max_length=2)

    def __str__(self):
        return f"{self.student.first_name} - {self.subject.name} - {self.grade_letter}"

