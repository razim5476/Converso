from django.urls import path
from a_users.views import *


urlpatterns = [
    path('', profile_view, name='profile'),
    path('edit/', profile_edit_view, name="profile-edit"),
    path('onboarding/', profile_edit_view, name="profile-onboarding"),
    path('settings/', profile_settings_view, name="profile-settings"),
    path('emailchange/', profile_emailchange, name="profile-emailchange"),
    path('emailverify/', profile_emailverify, name="profile-emailverify"),
    path('delete/', profile_delete_view, name="profile-delete"),
    path('add-friend/<str:username>/', send_friend_request, name='send-friend-request'),
    path('accept-friend/<str:username>/', accept_friend_request, name='accept-friend-request'),
    path('reject-friend/<str:username>/', reject_friend_request, name='reject-friend-request'),
    path('friend-requests/', friend_requests_view, name='friend-requests'),
    # View friends list
    path('friends/', friends_view, name='friends'),
    path('api/pending-request-count/',pending_requests_count_api,name="pending_request_count_api"),
]


