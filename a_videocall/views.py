from django.http import JsonResponse
from datetime import datetime, timedelta, timezone
import jwt
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
import os
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404
from a_rtchat.models import ChatGroup, GroupMessage
from a_users.models import Profile
from django.contrib.auth.models import User
from a_rtchat.models import Notification

@login_required
def video_dashboard(request):
    sender_profile = get_object_or_404(Profile, user=request.user)
    friends = sender_profile.friends.all()
    print(friends)
    return render(request, 'a_videocall/video_dashboard.html',{'name':request.user.username,'friends':friends})

def videocall_view(request):
    sender_profile = get_object_or_404(Profile, user=request.user)
    friends = sender_profile.friends.all()
    return render(request, 'a_videocall/videocall.html',{'name':request.user.username,'friends':friends})

@login_required
def join_room(request):
    if request.method == 'POST':
        roomID = request.POST['roomID']
        return redirect(f"/videocall/meeting?roomID={roomID}")
    return render(request, 'a_videocall/join_room.html')

def generate_kit_token(request):
    appID = int(os.getenv("ZEGO_APP_ID",1554908682))
    serverSecret = os.getenv("ZEGO_SERVER_SECRET","c5fdd8514823fa7bd225952d1ff55af2")
    
    roomID = request.GET.get('roomID','defaultRoom')
    userID = request.GET.get('userID',f"user_{datetime.now().timestamp()}")
    userName = request.GET.get('userName', f"Guest_{userID}")
    
    payload = {
        "appID": appID,
        "roomID": roomID,
        "userID": userID,
        "userName": userName,
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    
    token = jwt.encode(payload, serverSecret, algorithm="HS256")
    return JsonResponse({"kitToken": token})


def send_code_to_friends(request):
    if request.method == 'POST' and request.headers.get('HX-Request'):
        data = request.POST
        friends_ids = data.getlist("friends[]", [])
        code = data.get("body", "").strip()
        sender = request.user

        if not friends_ids:
            return JsonResponse({"error": "You must select at least one friend."}, status=400)
        if not code:
            return JsonResponse({"error": "Code cannot be empty."}, status=400)

        for friend_id in friends_ids:
            try:
                recipient = User.objects.get(id=friend_id)
                Notification.objects.create(
                    user=recipient,
                    message=f"{sender.username} Use this code to join the meeting: {code}",
                )
            except User.DoesNotExist:
                continue

        return JsonResponse({"success": "Code sent to selected friends as notifications."}, status=200)
    return JsonResponse({"error": "Invalid request."}, status=400)    

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-timestamp')
    data = {
        "notifications": [
            {"id": n.id, "message": n.message, "timestamp": n.timestamp} for n in notifications
        ]
    }
    return JsonResponse(data)


def mark_as_read(request, notification_id):
    if request.method == 'POST':  # Ensure we are only handling POST requests
        try:
            notification = Notification.objects.get(id=notification_id)
            notification.is_read = True
            notification.save()
            return JsonResponse({'status': 'success'})
        except Notification.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)