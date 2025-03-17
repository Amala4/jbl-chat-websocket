# Django imports
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required


# Django REST Framework imports
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.exceptions import NotFound

# Local imports
from .models import Message, Chat
from .serializers import MessageSerializer, UserSerializer, ChatListSerializer

# Constants
User = get_user_model()


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/signup.html', {'error': 'Username already exists'})
        
        user = User.objects.create_user(username=username, password=password)
        
        login(request, user)
        return redirect('index')  
    return render(request, 'accounts/signup.html')


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('index') 
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')



def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')  
    else:
        return redirect('index')



@login_required
def index(request):
    chat_list = get_chat_list(request.user)
    return render(request, "chats/index.html", {"chat_list": chat_list})



class UserListAPIView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.exclude(id=self.request.user.id)

    def list(self, request, *args, **kwargs):
        # return JSON to external consumer (mobile App) and html to web
        accept_header = request.headers.get('Accept', '')
        queryset = self.get_queryset()

        if 'application/json' in accept_header:
            serializer = self.get_serializer(queryset, many=True)
            return JsonResponse({"users": serializer.data}, safe=False)
        return render(request, "chats/user_list.html", {"user_list": queryset})



class ChatListAPIView(generics.ListAPIView):
    serializer_class = ChatListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        # return JSON to external consumer (mobile App) and html to web
        accept_header = request.headers.get('Accept', '')
        chat_list = get_chat_list(request.user)
        serializer = ChatListSerializer(chat_list, many=True)

        if 'application/json' in accept_header:
            return Response({"chat_list": serializer.data})
        
        return render(request, "chats/chat_list.html", {"chat_list": chat_list})



class UserSearchAPIView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id)
        search_query = self.request.GET.get('user_search', '').strip()
        
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        return queryset

    def list(self, request, *args, **kwargs):
        # return JSON to external consumer (mobile App) and html to web
        accept_header = request.headers.get('Accept', '')
        queryset = self.get_queryset()

        if 'application/json' in accept_header:
            serializer = self.get_serializer(queryset, many=True)
            return JsonResponse({"users": serializer.data}, safe=False)
        
        return render(request, "partials/user_search.html", {"user_list": queryset})



class ConversationAPIView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    other_user = None 

    def get_queryset(self):
        other_user_id = self.kwargs["user_id"]        
        try:
            self.other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            raise NotFound(detail="The user you are trying to chat with does not exist.")

        messages = Message.objects.filter(
            sender__in=[self.request.user, self.other_user],
            receiver__in=[self.request.user, self.other_user]
        ).order_by("timestamp")

        return messages

    def list(self, request, *args, **kwargs):
        # return JSON to external consumer (mobile App) and html to web
        accept_header = request.headers.get('Accept', '')
        queryset = self.get_queryset()

        if 'application/json' in accept_header:
            serializer = self.get_serializer(queryset, many=True)
            return JsonResponse(serializer.data, safe=False)

        context = {
            "messages": queryset, 
            "other_user": self.other_user
        }
        return render(request, "chats/conversation.html", context)



def get_chat_list(user):
    chats = Chat.objects.filter(participants=user).prefetch_related("participants", "messages")
    chat_list = []
    
    if chats:
        for chat in chats:
            latest_message = chat.messages.order_by('-timestamp').first() 
            other_user = chat.participants.exclude(id=user.id).first()
            if latest_message: 
                chat_list.append({
                    'latest_message': latest_message,
                    'latest_message_timestamp': latest_message.timestamp,
                    'other_user': other_user
                })
        chat_list.sort(key=lambda x: x['latest_message_timestamp'], reverse=True)

    return chat_list
