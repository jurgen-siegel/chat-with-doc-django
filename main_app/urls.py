
from django.urls import path
from . import views

urlpatterns = [
    path('upload_file/', views.upload_file, name='upload_file'),
]

    path('webui/', views.webui, name='webui'),

    path('process_query/', views.process_query, name='process_query'),


