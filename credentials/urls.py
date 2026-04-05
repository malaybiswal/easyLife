from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.credential_list, name='credential_list'),
    path('login/', auth_views.LoginView.as_view(template_name='credentials/login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('credential/edit/<int:pk>/', views.edit_credential, name='edit_credential'),
    path('credential/delete/<int:pk>/', views.delete_credential, name='delete_credential'),
    path('add/credential/', views.create_credential, name='create_credential'),
]
