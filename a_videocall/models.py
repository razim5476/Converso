from django.db import models
from a_rtchat.models import ChatGroup
from django.contrib.auth.models import User

class VideoCall(models.Model):
    chat_group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE)
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_calls_made')
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)