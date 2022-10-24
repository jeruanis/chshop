from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse

import json
from itertools import chain
from datetime import datetime
import pytz
from django.contrib import messages

from customer.models import FriendList
from accounts.models import Account
from chatapp.models import PrivateChatRoom, RoomChatMessage
from chatapp.utils import find_or_create_private_chat
from django.db.models import Q

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from shopme.settings import DEBUG
from datetime import date
current_date = date.today()

# create PRIVATE ROOM CHAT for SELLER
def private_chat_room_customer(request, *args, **kwargs):
    user = request.user  
    if user.is_authenticated:
        room_id = request.GET.get("room_id")
        context = {}
        if not room_id:
            context['m_and_f'] = get_recent_chatroom_messages(user)
        else:
            user2=PrivateChatRoom.objects.get(id=room_id).user2
            if user2 == user:
                user2 = PrivateChatRoom.objects.get(id=room_id).user1
            user2_id = Account.objects.get(email=user2).id
            room = PrivateChatRoom.objects.get((Q(user1=user) & Q(user2=user2)) | (Q(user2=user) & Q(user1=user2)), is_active=True)
            room_id = room.id
            if user == room.user1:
                user2 = room.user2
            else:
                user2 == room.user1
            context['m_and_f'] = get_recent_chatroom_messages(user)
            context["BASE_URL"] = settings.BASE_URL
            # context['debug'] = DEBUG
            context['debug_mode'] = settings.DEBUG
            context['room'] = room
            context['room_id'] = room_id
            context['user2'] = user2
            context['user2_id'] = user2_id
        return render(request, "chatapp/room.html", context)
    else:
        messages.warning(request, 'you are loggedout not authenticated')
        return redirect('store')


def private_chat_room_view(request, *args, **kwargs):
    user = request.user
    if not user.is_authenticated:
        return redirect('store')
    else:
        room_id = request.GET.get("room_id")
        group = str(user.group)
        admin_account= Account.objects.get(id=1, username__exact='chatme')
        context = {}
        if room_id == None: 
            if group == 'admin':
                try:
                    room = PrivateChatRoom.objects.filter(user1=user, is_active=True)
                    if room.count() > 1:
                        rooms=[]
                        for r in room:
                            rooms.append(r)
                        room = rooms[-1]
                        room_id = room.id
                        user2 = room.user2
                    else:
                        room = PrivateChatRoom.objects.get(user1=user, is_active=True)
                        room_id = room.id
                    user2 = room.user2

                except PrivateChatRoom.DoesNotExist:
                    room = PrivateChatRoom.objects.filter(user2=user, is_active=True)
                    if room.count() > 1:
                        rooms=[]
                        for r in room:
                            rooms.append(r)
                        room = rooms[-1]
                        room_id = room.id
                        user2 = room.user1
                    else:
                        room = PrivateChatRoom.objects.get(user2=user, is_active=True)
                        room_id = room.id
                    user2 = room.user1

            else: 
                try:
                    room = PrivateChatRoom.objects.get(Q(user1=user) | Q(user2=user), is_active=True)
                    room_id = room.id
                    if user == room.user1:
                        user2 = room.user2
                    else:
                        user2 == room.user1

                except PrivateChatRoom.DoesNotExist:
                    admin_friendlist = FriendList.objects.get(user=admin_account)
                    user = Account.objects.get(id=user.id) 
                    if user in admin_friendlist.friends.all():
                        chat = find_or_create_private_chat(user, admin_account) 
                        room = PrivateChatRoom.objects.get(Q(user1=user) | Q(user2=user), is_active=True) #query the room
                        room_id = room.id
                        if user == room.user1:
                            user2 = room.user2
                        else:
                            user2 == room.user1
                    else:
                        pass
        else: 
            room = PrivateChatRoom.objects.get(id=room_id, is_active=True)
            if room.user1 == user:
                user2 = room.user2
            else:
                user2 = room.user1
        context['m_and_f'] = get_recent_chatroom_messages(user)
        context["BASE_URL"] = settings.BASE_URL
        # context['debug'] = DEBUG
        context['debug_mode'] = settings.DEBUG
        context['room'] = room
        context['room_id'] = room_id
        context['user2'] = user2
        return render(request, "chatapp/room.html", context)

def get_recent_chatroom_messages(user):
    """
    sort in terms of most recent chats (users that you most recently had conversations with)
    """
    rooms1 = PrivateChatRoom.objects.filter(user1=user, is_active=True)
    rooms2 = PrivateChatRoom.objects.filter(user2=user, is_active=True)

    rooms = list(chain(rooms1, rooms2))

    m_and_f = []
    for room in rooms:
        if room.user1 == user:
            friend = room.user2
        else:
            friend = room.user1
        try:
            message = RoomChatMessage.objects.filter(room=room).latest("timestamp")
        except RoomChatMessage.DoesNotExist:
            today = datetime(
            	year=current_date.year,
            	month=current_date.month,
            	day=current_date.day,
            	hour=1,
            	minute=1,
            	second=1,
            	tzinfo=pytz.UTC
            )
            message = RoomChatMessage(
            	user=friend,
            	room=room,
            	timestamp=today,
            	content="",
            )
        m_and_f.append({
        'message': message,
        'friend': friend,
        'room_id':room,
        })
    return sorted(m_and_f, key=lambda x: x['message'].timestamp, reverse=True)


@login_required(login_url='login')
def create_or_return_private_chat(request):
    user1 = request.user
    payload = {}
    if user1.is_authenticated:
        if request.method == "POST":
            user2_id = request.POST.get("user2_id") 
            try:
                user2 = Account.objects.get(pk=user2_id) 
                friendlist = FriendList.objects.get(user=user1)
                user2_friendlist = FriendList.objects.get(user=user2)
                if user2 in friendlist.friends.all():
                    pass
                else:
                    friendlist.friends.add(user2)
                    friendlist.save()
                if user1 in user2_friendlist.friends.all():
                    pass
                else:
                    user2_friendlist.friends.add(user1)
                    user2_friendlist.save()
                chat = find_or_create_private_chat(user1, user2)
                payload['response'] = "Successfully got the chat."
                payload['chatroom_id'] = chat.id
                payload['user2_id']  = user2_id
            except Account.DoesNotExist:
                payload['response'] = "Unable to start a chat with that user."
        else:
            payload['response'] = "You can't start a chat if you are not authenticated."
        return HttpResponse(json.dumps(payload), content_type="application/json")
    else:
        messages.warning(request, 'You have to login to be able to chat')
        return redirect('login')
