from .models import Cart, CartItem
from .views import _cart_id
from accounts.models import Account
import json
import requests
from urllib.parse import urlparse
from decouple import config
from django.shortcuts import redirect
from django.core.cache import cache

def counter(request):
    cart_count=0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=_cart_id(request))
            if request.user.is_authenticated:
                cart_items = CartItem.objects.all().filter(user=request.user)
                for cart_item in cart_items:
                    cart_count += cart_item.quantity
            else:
                cart_items = CartItem.objects.all().filter(cart_id=cart[:1])
                for cart_item in cart_items:
                    cart_count += cart_item.quantity
        except Cart.DoesNotExist:
            cart_count = 0

    return dict(cart_count=cart_count)


def country_cur(request):
    url = request.build_absolute_uri()
    x_forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO') 
    ip_add = request.META.get('REMOTE_ADDR')
    if url is not None:
        o = urlparse(url)
        proto = o.scheme
    elif x_forwarded_proto == 'https':
        proto = 'https'
    elif x_forwarded_proto == 'http':
        proto = 'http'
    elif ip_add == '127.0.0.1':
        proto = 'http' 
    else:
        proto = 'https' 

    if proto == 'https':
        req = requests.get('http://ip-api.com/json?fields=country,countryCode,currency')
        dict_result = req.json()
        country = dict_result ['country'] 
        country_code = dict_result ['countryCode']
        currency = dict_result ['currency']
    else:
        country = 'Philippines' 
        country_code = 'PH'
        currency = 'PHP'

    logout='logout'
    user = request.user
    user_id = user.id

    if user.is_authenticated: 
        accounts = Account.objects.get(email=user)
        country = accounts.country

    if country == 'Philippines':
        currency='PHP'
        symbol = '₱'
        country_code = 'PH'
    elif country == 'United States':
        currency = 'USD'
        symbol = '$'
        country_code = 'US'
    else:
        country = country
        currency = 'USD'
        symbol = '$'
        country_code = country_code


    return dict(currency=currency, symbol=symbol, country=country, user_id=user_id, logout=logout, protocol=proto)
