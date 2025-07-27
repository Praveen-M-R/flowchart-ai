from django.urls import path
from . import views

urlpatterns = [
    path('repositories/', views.list_repositories, name='list_repositories'),
]
