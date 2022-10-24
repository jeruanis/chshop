from django.contrib import admin
from .models import Cart, CartItem

class CartAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'date_added')
    readonly_fields = ('cart_id',)

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'cart', 'quantity', 'is_active', 'cart_id')

admin.site.register(Cart, CartAdmin)
admin.site.register(CartItem, CartItemAdmin)
