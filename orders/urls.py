from django.urls import path
from . import views

urlpatterns = [
    path('place_order/', views.place_order, name='place_order'),
    path('payments/', views.payments, name='payments'),
    path('item_recieved/<int:order_number>/', views.item_recieved, name='item_recieved'),
    path('paySeller/<int:order_number>/', views.paySeller, name='paySeller'),
    path('order_complete/', views.order_complete, name='order_complete'),
    path('update_order_status/<str:pk>/', views.update_order_status, name='update_order_status'),
    path('update_status_cancel/<str:pk>/', views.update_status_cancel, name='update_status_cancel'),
    path('deleted_order/<str:pk>/', views.deleted_order, name='deleted_order'),
    path('deleteOrder/<str:pk>/', views.deleteOrder, name='deleteOrder'),
    path('order_detail/<int:order_number>/', views.order_detail, name='order_detail'),

]
