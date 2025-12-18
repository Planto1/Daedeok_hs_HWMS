# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.fire_map_view, name='fire_map'),  # 메인 페이지
    path('api/fire-data/', views.fire_data_api, name='fire_data_api'),
    path('refresh-data/', views.load_and_save_fire_data, name='refresh_data'),
]