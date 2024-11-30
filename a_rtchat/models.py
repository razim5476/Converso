from django.db import models
from django.contrib.auth.models import User
import os
import shortuuid
from PIL import Image
from django.core.mail import send_mail

# Create your models here.

class ChatGroup(models.Model):
    group_name = models.CharField(max_length=128, unique=True, default=shortuuid.uuid)
    groupchat_name = models.CharField(max_length=128, null=True, blank=True)
    admin = models.ForeignKey(User, related_name="groupchats", blank=True, null=True ,on_delete=models.SET_NULL)
    users_online = models.ManyToManyField(User, related_name='online_in_groups', blank=True)
    members = models.ManyToManyField(User, related_name='chat_groups', blank=True)
    is_private = models.BooleanField(default=False)
    description = models.TextField(null=True,blank=True)
    groupchat_type = models.CharField(max_length=20, choices=[
        ('private', 'Private'),
        ('group', 'Group'),
    ])
    
    def __str__(self):
        return self.group_name
    
    def invite_user(self, email, inviter):
        subject = f"{inviter.username} invited you to join the group '{self.groupchat_name}'"
        message = f"Hi, {inviter.username} has invited you to join the group '{self.groupchat_name}'.\n\nClick the link below to join:\nhttp://127.0.0.1:8000/join_group/{self.id}/"
        from_email = 'converso402@gmail.com'
        
        send_mail(subject, message, from_email, [email])
    
class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup, related_name='chat_messages', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length=300, blank=True, null=True)
    file = models.FileField(upload_to='files/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    
    @property
    def filename(self):
        if self.file:
            return os.path.basename(self.file.name)
        else:
            return None
    
    def __str__(self):
        if self.body:
            return f'{self.author.username} : {self.body}'
        elif self.file:
            return f'{self.author.username} : {self.filename}'
    
    class Meta:
        ordering = ['-created']
        
    @property
    def is_image(self):
        try:
            image = Image.open(self.file)
            image.verify()
            return True
        except:
            return False
        
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)