from django.urls import path
from . import views
from .views import (
    UserListAPIView,
    ConversationAPIView,
    ChatListAPIView,  
    UserSearchAPIView  
)

urlpatterns = [
    
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    path("", views.index, name="index"),
    path("users/", UserListAPIView.as_view(), name="user_list"),
    path("user-search/", UserSearchAPIView.as_view(), name="user_search"),
    path("chats/", ChatListAPIView.as_view(), name="chat_list"),
    path("chat/<int:user_id>/", ConversationAPIView.as_view(), name="conversation"),
]

