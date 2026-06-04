from django.urls import path
from . import views

urlpatterns = [
    # Authentication paths
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Event paths
    path('', views.event_list, name='event_list'),
    path('events/', views.all_events, name='all_events'),
    path('event/new/', views.event_create, name='event_create'),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('event/<int:pk>/edit/', views.event_update, name='event_update'),
    path('event/<int:pk>/delete/', views.event_delete, name='event_delete'),
    path('event/<int:pk>/mark-paid/', views.mark_as_paid, name='event_mark_paid'),
    path('event/<int:pk>/update-status/', views.event_update_status, name='event_update_status'),
]
