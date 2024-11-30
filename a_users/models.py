from django.db import models
from django.contrib.auth.models import User
from django.templatetags.static import static
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='avatars/',null=True,blank=True)
    displayname = models.CharField(max_length=20,null=True,blank=True)
    info = models.TextField(null=True,blank=True)
    friends = models.ManyToManyField(User, related_name='friends', blank=True)
    in_call = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {'In Call' if self.in_call else 'Available'}"
    
    @property
    def name(self):
        if self.displayname:
            name = self.displayname
        else:
            name = self.user.username
        return name
    
    @property
    def avatar(self):
        try:
            avatar = self.image.url
        except:
            avatar = static('images/avatar.svg')
        return avatar
    
class Friendship(models.Model):
    sender = models.ForeignKey(User, related_name="send_request",on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_requests",on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=(
            ('pending', 'pending'),
            ('accepted', 'accepted'),
            ('rejected', 'rejected'),
        ),
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('sender', 'receiver')
        
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.status})"