# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.fire_map_view, name='fire_map'),
    path('api/fire-data/', views.fire_data_api, name='fire_data_api'),
    path('api/fetch-save/', views.fetch_and_save_fire_data, name='fetch_save'),
    path('api/stats/', views.fire_stats_api, name='fire_stats'),
    path('refresh-data/', views.load_and_save_fire_data, name='refresh_data'),
]