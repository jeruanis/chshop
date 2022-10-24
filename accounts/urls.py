from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard_single/', views.dashboard_single, name='dashboard_single'),
    path('', views.dashboard, name='dashboard'),
    path('my_profile/', views.my_profile, name='my_profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('change_password/', views.change_password, name='change_password'),

    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('forgotPasswordResetValidate/<uidb64>/<token>/', views.forgotPasswordResetValidate, name='forgotPasswordResetValidate'),
    path('forgotPassword/', views.forgotPassword, name='forgotPassword'),
    path('forgotPasswordReset_page/', views.forgotPasswordReset_page, name='forgotPasswordReset_page'),

    path('<int:user_id>/', views.account_view, name="view"),#needed fot chat
    path('<int:user_id>/edit/cropImage/', views.crop_image, name="crop_image"),
    path('my_store_order/', views.my_store_order, name='my_store_order'),


]
