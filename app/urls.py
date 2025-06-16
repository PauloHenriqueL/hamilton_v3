from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

#Template
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', auth_views.LoginView.as_view(), name='login'),


#Api
    path('api/v1/', include('principais.urls')),
    path('api/v1/', include('acessorios.urls')),
]
