from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.db.models import Q
from a_users.models import *
from .forms import *
from channels.layers import get_channel_layer

def profile_view(request, username=None):
    if username:
        profile = get_object_or_404(User, username=username).profile
    else:
        try:
            profile = request.user.profile
        except:
            return redirect_to_login(request.get_full_path())
    return render(request, 'a_users/profile.html', {'profile':profile})


@login_required
def profile_edit_view(request):
    form = ProfileForm(instance=request.user.profile)  
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
        
    if request.path == reverse('profile-onboarding'):
        onboarding = True
    else:
        onboarding = False
      
    return render(request, 'a_users/profile_edit.html', { 'form':form, 'onboarding':onboarding })


@login_required
def profile_settings_view(request):
    return render(request, 'a_users/profile_settings.html')


@login_required
def profile_emailchange(request):
    
    if request.htmx:
        form = EmailForm(instance=request.user)
        return render(request, 'partials/email_form.html', {'form':form})
    
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)

        if form.is_valid():
            
            # Check if the email already exists
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.warning(request, f'{email} is already in use.')
                return redirect('profile-settings')
            
            form.save() 
            
            # Then Signal updates emailaddress and set verified to False
            
            # Then send confirmation email 
            send_email_confirmation(request, request.user)
            
            return redirect('profile-settings')
        else:
            messages.warning(request, 'Form not valid')
            return redirect('profile-settings')
        
    return redirect('home')


@login_required
def profile_emailverify(request):
    send_email_confirmation(request, request.user)
    return redirect('profile-settings')


@login_required
def profile_delete_view(request):
    user = request.user
    if request.method == "POST":
        logout(request)
        user.delete()
        messages.success(request, 'Account deleted, what a pity')
        return redirect('home')
    
    return render(request, 'a_users/profile_delete.html')

# friend request:

@login_required
def send_friend_request(request, username):
    receiver = get_object_or_404(User, username=username)
    
    if request.user == receiver:
        messages.warning(request, "You can't send a friend request to yourself.")
        return redirect('profile', username=username)
    
    # Check if there's an existing request
    existing_request = Friendship.objects.filter(sender=request.user, receiver=receiver).first()
    
    if existing_request:
        if existing_request.status == 'accepted':
            messages.info(request, "You are already friends with this user.")
        else:
            messages.warning(request, "You have already sent a friend request.")
    else:
        Friendship.objects.create(sender=request.user, receiver=receiver, status='pending')
        messages.success(request, "Friend request sent.")
    
    return redirect('profile', username=username)

@login_required
def accept_friend_request(request, username):
    # Fetch the sender user object based on the username passed in the URL
    sender = get_object_or_404(User, username=username)

    # Try to fetch the friendship with status 'pending'
    friendship = get_object_or_404(Friendship, sender=sender, receiver=request.user, status='pending')

    # Change the friendship status to 'accepted'
    friendship.status = 'accepted'
    friendship.save()

    # Add both users to each other's friends list (Profile -> friends)
    request.user.profile.friends.add(sender)  # Add sender to receiver's friends list
    sender.profile.friends.add(request.user)  # Add receiver to sender's friends list

    # Optionally, create a reciprocal friendship if needed
    Friendship.objects.get_or_create(sender=request.user, receiver=sender, status='accepted')

    # Show success message and redirect
    messages.success(request, "Friend request accepted.")
    return redirect('profile', username=username)


# Reject Friend Request
@login_required
def reject_friend_request(request, username):
    friendship = get_object_or_404(Friendship, sender=username, receiver=request.user, status='pending')
    friendship.status = 'rejected'
    friendship.save()
    
    messages.success(request, "Friend request rejected.")
    return redirect('profile', username=username)

@login_required
def friend_requests_view(request):
    # Fetch the user's pending, accepted, and rejected requests
    pending_requests = Friendship.objects.filter(receiver=request.user, status='pending')
    accepted_requests = Friendship.objects.filter(
        (Q(sender=request.user) | Q(receiver=request.user)), status='accepted')
    rejected_requests = Friendship.objects.filter(
        (Q(sender=request.user) | Q(receiver=request.user)), status='rejected')

    return render(request, 'a_users/friend_request.html', {
        'pending_requests': pending_requests,
        'accepted_requests': accepted_requests,
        'rejected_requests': rejected_requests,
    })
    
def friends_view(request):
    friends = request.user.profile.friends.all()
    return render(request, 'a_users/friends.html',{'friends':friends})

def pending_requests_count_api(request):
    if request.user.is_authenticated:
        # Filter by status="pending"
        count = Friendship.objects.filter(receiver=request.user, status="pending").count()
    else:
        count = 0
    return JsonResponse({'pending_requests_count': count})