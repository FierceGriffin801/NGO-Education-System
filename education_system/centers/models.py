from django.db import models
from django.contrib.auth.models import User

class Center(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=300)
    coordinator = models.ForeignKey(User, on_delete=models.CASCADE)
    established_date = models.DateField()
    capacity = models.IntegerField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name
