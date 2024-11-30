from django.urls import path
from .views import *
from . import views


app_name = 'a_videocall'

urlpatterns=[
    path('video_call/', video_dashboard, name='video_call'),
    path('meeting/',videocall_view,name="meeting"),
    path('join_room/',join_room,name='join_room'),
    path('api/generate_kit_token/', generate_kit_token, name='generate_kit_token'),
    path('send_code_to_friends/', views.send_code_to_friends, name='send_code_to_friends'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/mark-as-read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
]