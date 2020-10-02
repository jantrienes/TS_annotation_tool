from django.urls import path, re_path, include
from . import views

urlpatterns = [
    path('insertion', views.insert_data, name="insert_data"),
    path('home', views.home, name="home"),
]
