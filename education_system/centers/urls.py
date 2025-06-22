from django.urls import path
from . import views

urlpatterns = [
    path('', views.center_list, name='center_list'),
    path('<int:center_id>/', views.center_detail, name='center_detail'),
]
