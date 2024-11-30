from django.shortcuts import render,get_object_or_404,redirect
from . models import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from . forms import *
from django.http import Http404
from django.contrib import messages
from django.contrib.messages import success
# Create your views here.

@login_required
def chat_view(request, chatroom_name='public-chat'):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    chat_messages = chat_group.chat_messages.all()[:30]
    form = ChatMessageCreateForm()
    
    other_user = None
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404()
        for member in chat_group.members.all():
            if member != request.user:
                other_user = member
                break
            
    
    if chat_group.groupchat_name:
        if request.user not in chat_group.members.all():
            if request.user.emailaddress_set.filter(verified=True).exists():
                chat_group.members.add(request.user)
            else:
                messages.warning(request, 'You need to verify your email to join the chat!')
                return redirect('profile-settings')
        
    if request.htmx:
        form = ChatMessageCreateForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            context = {
                'message': message,
                'user':request.user
            }
            return render(request, 'a_rtchat/partials/chat_message_p.html', context)
    
    
    context = {
        'chat_messages': chat_messages,
        'form' : form,
        'other_user' : other_user,
        'chatroom_name' : chatroom_name,
        'chat_group' : chat_group,
    }    
    return render(request, 'a_rtchat/chat.html',context)


def get_or_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')
    
    other_user = User.objects.get(username = username)
    my_private_chatrooms = request.user.chat_groups.filter(is_private=True)
    
    if my_private_chatrooms.exists():
        for chatroom in my_private_chatrooms:
            if other_user in chatroom.members.all():
                return redirect('chatroom',chatroom.group_name)
           
                
    
    chatroom = ChatGroup.objects.create(is_private = True)
    chatroom.members.add(other_user, request.user)
        
    return redirect('chatroom', chatroom.group_name)


@login_required
def create_groupchat(request):
    # Retrieve friends from the user's profile
    friends = request.user.profile.friends.all()  
    
    if request.method == 'POST':
        # Initialize the form with POST data and filtered friends as the queryset
        form = NewGroupForm(request.POST, user=request.user)
        form.fields['members'].queryset = friends  
    else:
        # Initialize the form with filtered friends as the queryset
        form = NewGroupForm(user=request.user)
        form.fields['members'].queryset = friends  
    
    # Debugging: Check the queryset being passed to the form
    print(f"Form members queryset: {form.fields['members'].queryset}")

    if form.is_valid():
        # Create the new group chat
        new_groupchat = form.save(commit=False)
        new_groupchat.admin = request.user
        new_groupchat.save()
        new_groupchat.members.add(request.user, *form.cleaned_data['members'])
        return redirect('chatroom', new_groupchat.group_name)

    context = {'form': form}
    return render(request, 'a_rtchat/create_groupchat.html', context)



    
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

@login_required
def chatroom_edit_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.admin:
        raise Http404()

    form = ChatRoomEditForm(instance=chat_group)
    available_friends = request.user.profile.friends.exclude(id__in=chat_group.members.all())

    if request.method == "POST":
        form = ChatRoomEditForm(request.POST, instance=chat_group)
        if form.is_valid():
            form.save()

            channel_layer = get_channel_layer()

            # Handle removed members
            remove_members = request.POST.getlist('remove_members')
            for member_id in remove_members:
                member = User.objects.get(id=member_id)
                chat_group.members.remove(member)

                # Notify the removed user in real-time
                async_to_sync(channel_layer.group_send)(
                    f"user_{member.username}",
                    {
                        "type": "user_removed",  # Custom event type
                        "message": f"You have been removed from the group '{chat_group.groupchat_name}' by the admin.",
                        "redirect_url": "/public_chat/",  # URL to redirect the user to
                    },
                )

            # Handle added members
            add_members = request.POST.getlist('add_members')
            for member_id in add_members:
                member = User.objects.get(id=member_id)
                chat_group.members.add(member)

            return redirect('chatroom', chatroom_name)

    context = {
        'form': form,
        'chat_group': chat_group,
        'available_friends': available_friends,
    }
    return render(request, 'a_rtchat/chatroom_edit.html', context)


@login_required
def chatroom_delete_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.admin:
        raise Http404()
    
    if request.method == "POST":
        chat_group.delete()
        messages.success(request, 'Chatroom deleted')
        return redirect('home')
    
    return render(request, 'a_rtchat/chatroom_delete.html',{'chat_group':chat_group})


@login_required
def chatroom_leave_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user not in chat_group.members.all():
        raise Http404()
    
    if request.method == "POST":
        chat_group.members.remove(request.user)
        messages.success(request, 'You have left the chatroom')
        return redirect('home')
    
def chat_file_upload(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.htmx and request.FILES:
        file = request.FILES['file']
        
        if not file:
            return HttpResponse("No file provided.", status=400)
        
        message = GroupMessage.objects.create(
            file = file,
            author = request.user,
            group = chat_group,
        )
        channel_layer = get_channel_layer()
        event = {
            'type': 'message_handler',
            'message_id': message.id,
        }
        async_to_sync(channel_layer.group_send)(
            chatroom_name, event
        )
    return HttpResponse()






from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import urlencode
from django.conf import settings

@login_required
def invite_user(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)


    if request.method == "POST":
        form = InviteForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            
            # Generate a link for joining the group
            join_url = request.build_absolute_uri(
                reverse('join-group') + '?' + urlencode({'group_id': group.id})
            )
            
            # Send email invitation
            send_mail(
                subject="You're Invited to Join a Group!",
                message=f"You have been invited to join the group '{group.groupchat_name}'. Click the link to join: {join_url}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
            )
            
            messages.success(request, f"Invitation sent to {email}")
            return redirect('chatroom', chatroom_name=group.group_name)
    else:
        form = InviteForm()

    return render(request, 'a_rtchat/invite_user.html', {'form': form, 'group': group})


@login_required
def join_group(request):
    group_id = request.GET.get('group_id')
    if not group_id:
        messages.error(request, "Invalid join link.")
        return redirect('home')
    
    group = get_object_or_404(ChatGroup, id=group_id)
    
    if request.user in group.members.all():
        messages.warning(request, "You are already a member of this group.")
    else:
        group.members.add(request.user)
        messages.success(request, f"You have joined the group '{group.groupchat_name}'.")

    return redirect('chatroom', chatroom_name=group.group_name)



