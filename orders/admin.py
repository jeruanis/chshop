from django.contrib import admin
from .models import Payment, Order, OrderProduct

class OrderPrductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra  = 0 

class OrderProductAdmin(admin.ModelAdmin):
    list_display  = ('payment', 'user', 'product', 'quantity', 'ordered', 'status', 'is_deleted', 'for_payment', 'paid')
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'total_price', 'ordered')
    list_filter = ('ordered',)
    search_fields = ('product__product_name','user__email', 'payment__payment_id', 'deleted')
    fields=['payment', 'variation', 'status', 'ip', 'user', 'product', 'quantity', 'product_price', 'total_price','ordered', 'recieved', 'is_deleted', 'for_payment', 'paid', 'request_payment', 'is_refund', 'cus_ref_accept_del', 'cus_item_delete']


class OrderAdmin(admin.ModelAdmin):
    list_display = ('fullname', 'email', 'currency', 'order_total', 'status', 'payment', 'updated_at', 'is_ordered')
    list_filter = ('status', 'is_ordered')
    search_fields = ('order_number', 'first_name', 'last_name', 'phone', 'email', 'updated_at')
    list_per_page = 20 
    inlines = [OrderPrductInline] 

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'user', 'amount_paid', 'status')

admin.site.register(Payment, PaymentAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)
