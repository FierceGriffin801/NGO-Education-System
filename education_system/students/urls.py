from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('<int:student_id>/', views.student_detail, name='student_detail'),
    path('add/', views.add_student, name='add_student'),
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('grades/', views.grade_list, name='grade_list'),
    path('grades/add/', views.add_grade, name='add_grade'),
]
