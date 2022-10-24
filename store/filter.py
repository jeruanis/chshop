import django_filters
from django_filters import DateFilter, CharFilter, BooleanFilter
from .models import Product
from django import forms
from orders.models import OrderProduct


class ProductPriceFilter(django_filters.FilterSet):
    min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    class Meta:
        model = Product  
        fields = ['price']

class OrderProductFilter(django_filters.FilterSet):
    class Meta:
        model = OrderProduct
        fields = ['for_payment', 'request_payment', 'status', 'product__added_by']

class OrderProductFilterSeller(django_filters.FilterSet):
    for_payment =  django_filters.BooleanFilter()
    status = django_filters.CharFilter(max_length=25)

    class Meta:
        model = OrderProduct
        fields = ['for_payment', 'request_payment', 'status']
