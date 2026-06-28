from django.urls import path

from expenses import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
