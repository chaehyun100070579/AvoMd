from django.urls import path
from . import views

urlpatterns = [
    path('', views.create_job, name='create_job'),
    path('<uuid:event_id>/', views.get_job_status, name='get_job_status'),
]