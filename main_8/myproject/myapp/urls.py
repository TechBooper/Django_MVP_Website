from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from .views import dashboard

app_name = 'myapp'


urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('feed/', views.feed, name='feed'),
    path('base/', views.index, name='base'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('create_ticket/', views.create_ticket, name='create_ticket'),
    path('create_review/<int:ticket_id>/', views.create_review, name='create_review'),
    path('create_ticket_review/', views.create_ticket_review, name='create_ticket_review'),
    path('follow_user/', views.follow_user, name='follow_user'),
    path('unfollow_user/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('followed_users/', views.followed_users, name='followed_users'),
    path('add_ticket/', views.add_ticket, name='add_ticket'),
    path('edit_ticket/<int:ticket_id>/', views.edit_ticket, name='edit_ticket'),
    path('delete_ticket/<int:ticket_id>/', views.delete_ticket, name='delete_ticket'),
    path('add_review/', views.add_review, name='add_review'),
    path('edit_review/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete_review/<int:review_id>/', views.delete_review, name='delete_review'),
    path('accounts/', include('django.contrib.auth.urls')),
]
