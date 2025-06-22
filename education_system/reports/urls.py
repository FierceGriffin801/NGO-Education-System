from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_dashboard, name='reports'),
    path('generate/', views.generate_report, name='generate_report'),
    path('list/', views.report_list, name='report_list'),
    path('<int:report_id>/', views.report_detail, name='report_detail'),
    path('<int:report_id>/download/', views.download_report, name='download_report'),
]

