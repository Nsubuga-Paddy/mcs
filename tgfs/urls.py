from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'tgfs'

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup_view, name='signup'),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('member-dashboard/', views.member_dashboard_view, name='member_dashboard'),
    path('members/', views.members_view, name='members'),
    path('download-savings/', views.download_savings, name='download_savings'),
    # Add other URLs like login, dashboard, etc. when needed
]
