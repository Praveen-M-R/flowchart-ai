from django.urls import path
from . import views

urlpatterns = [
    path('generate_flowchart/', views.generate_flowchart_view, name='generate_flowchart'),
]
