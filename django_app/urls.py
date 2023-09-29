from django.urls import path
from main_app import views

urlpatterns = [
    path('', views.webui, name='webui'),
    path('process_query/', views.process_query, name='process_query'),
]
