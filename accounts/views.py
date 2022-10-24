from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegistrationForm, EditProfileForm, UserProfilePicForm, PwdChangeForm, LoginForm
from .models import Account
from django.contrib import messages, auth
from django.contrib.auth.decorators import login_required
from .decorators import allowed_users
from orders.models import OrderProduct, Order

from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from carts.models import CartItem, Cart
from carts.views import _cart_id
from store.models import Product
from django.db.models import Q
import requests

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.http import HttpResponse

from customer.models import FriendList, FriendRequest
from customer.friend_request_status import FriendRequestStatus
from customer.utils import get_friend_request_or_false
from django.conf import settings
from customer.models import FriendList
import datetime

import os
import cv2
import json
import base64

from django.core import files
from django.core.files.storage import default_storage
from django.core.files.storage import FileSystemStorage
from django.core.cache import cache
from django.contrib.sessions.models import Session
from django.core.cache import cache # This is the memcache cache.

from store.filter import  OrderProductFilter, OrderProductFilterSeller

from rest_framework.authtoken.models import Token


TEMP_PROFILE_IMAGE_NAME = "temp_profile_image.png"

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        group = Group.objects.get(name='Customer')
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            phone = form.cleaned_data['phone']
            country = form.cleaned_data['country']
            password = form.cleaned_data['confirm_password']
            username = email.split('@')[0]

            user = Account.objects.only('username')
            username_list =[]
            for n in user:
                username_list.append(n.username)
            for uname in username_list:
                if username == uname:
                    username = username + str(-3)
                    num = username.split('-')[1]
                    ustring = username.split('-')[0]
                    conv_num = int(num)
                    num = conv_num+1
                    username = ustring+'-'+str(num)
                else:
                    username == username

            user = Account.objects.create_user(first_name=first_name, last_name=last_name, email=email, password=password, username=username)

            user.phone=phone
            user.country = country
            user.group=group
            user.save()

            admin_account= Account.objects.get(id=1, username__exact='chatme')
            admin_friendlist = FriendList.objects.get(user=admin_account)
            user = Account.objects.get(id=user.id)
            if not user in admin_friendlist.friends.all():
                admin_friendlist.friends.add(user)
                admin_friendlist.save()

            add_admin_friend = FriendList.objects.create(user=user)
            add_admin_friend.friends.add(admin_account)
            add_admin_friend.save()

            api_token = Token.objects.create(user=user)

            current_site = get_current_site(request)
            mail_subject = 'JV Store Account Activation'
            message = render_to_string('accounts/account_verification_email.html', {
                'user':user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            msg1 = "We have sent a verification email to "+ email +". Please confirmed it first to be able to login."
            msg2 = "Your API Key is "+ str(api_token) +" copy and keep this in secure place, do not share to anyone. You need this to access the JV-STORE API."
            messages.warning(request, msg1 )
            messages.warning(request, msg2)
            return redirect('/accounts/login/')
    else:
        form = RegistrationForm()

    context= {'form':form}
    return render(request, 'accounts/register.html', context)


def login(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user=auth.authenticate(email=email, password=password)
        orderproduct = OrderProduct.objects.filter(user=user)
        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request)) #get the session id
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                if is_cart_item_exists:
                    cart_item = CartItem.objects.filter(cart=cart)
                    products=[]

                    for i in cart_item:
                        product_id = i.product_id
                        product = Product.objects.get(id=product_id)
                        products.append(product)

                    cart_item_cart_list=[]
                    for p in products:
                        cart_item_cart = CartItem.objects.filter(product=p, cart=cart)
                        cart_item_cart_list.append(cart_item_cart)

                    cart_item_user = CartItem.objects.filter(user=user)

                    item_carts={}
                    for item in cart_item_cart_list:
                        for i in item:
                            id=i.id
                            qty = i.quantity
                            prod_id = i.product_id
                            variation = i.variations.all()
                            variation = list(variation)
                            variation=str(variation)
                            item_carts[variation+str(prod_id)]=(str(qty) + '-' + str(id))

                    id=[]
                    item_user=[]
                    for item in cart_item_user:
                        id.append(item.id)

                    for item in cart_item_user:
                        qty = item.quantity
                        prod_id = item.product_id
                        variation = item.variations.all()
                        variation = list(variation)
                        variation=str(variation)
                        item_user.append(variation+str(prod_id))

                    id_cart =[]
                    for key, value in item_carts.items():
                        if key in item_user:
                            index = item_user.index(key)
                            item_id = id[index]
                            item = CartItem.objects.get(id=item_id)
                            product = item.product
                            stock = product.stock
                            qty_value=int(value.split('-')[0])
                            id_used = int(value.split('-')[1])
                            id_cart.append(id_used)
                            item.quantity +=qty_value

                            item.user = user
                            item.save()

                        else:
                            if len(id_cart) == 0:
                                for item in cart_item:
                                    item.user = user
                                    item.save()

                            else:

                                for i in id_cart:
                                    del_cart_item = CartItem.objects.get(id=id_cart[id_cart.index(i)])
                                    cart_item = CartItem.objects.filter(cart=cart).exclude(id=id_cart[id_cart.index(i)])
                                    for item in cart_item:
                                        item.user = user
                                        item.save()

                                    del_cart_item.delete()
                    url = request.META.get('HTTP_REFERER')
                    cart_item_user = CartItem.objects.filter(user=user)
                    if cart_item_user.count() > 0:
                        try:
                            query = requests.utils.urlparse(url).query
                            params = dict(x.split('=') for x in query.split('&'))
                            if 'next' in params:
                                if params['next'] == '/cart/checkout/':
                                    nextPage = params['next']
                                    auth.login(request, user)
                                    messages.success(request, 'You are now loggedin.')
                                    return redirect(nextPage)
                                else:
                                    messages.warning(request, 'That page cannot be accesed directly')
                                    return redirect('login')

                        except ValueError:
                            if orderproduct.count() > 0: 
                                auth.login(request, user)
                                messages.success(request, 'You are now loggedin.')
                                return redirect('dashboard')
                            else:
                                auth.login(request, user)
                                return redirect('home')
                    elif orderproduct.count() > 0: 
                        auth.login(request, user)
                        messages.success(request, 'You are now loggedin.')
                        return redirect('dashboard')

                    else:
                        auth.login(request, user)
                        return redirect('home')
                else:
                    auth.login(request, user)
                    cart_item_user = CartItem.objects.filter(user=user)
                    if cart_item_user.count() > 0: 
                        auth.login(request, user)
                        return redirect('checkout')
                    elif orderproduct.count() > 0: 
                        auth.login(request, user)
                        return redirect('dashboard')
                    else:
                        auth.login(request, user)
                        return redirect('home')

            except Cart.DoesNotExist:
                auth.login(request, user)
                cart_item_user = CartItem.objects.filter(user=user)
                if cart_item_user.count() > 0: 
                    auth.login(request, user)
                    return redirect('checkout')
                elif orderproduct.count() > 0: 
                    auth.login(request, user)
                    return redirect('dashboard')
                else:
                    auth.login(request, user)
                    return redirect('home')
        else: 
            messages.warning(request, 'Username or Password is incorrect!')
            return redirect('login')
    else: 
        form=LoginForm()
        context={'form':form}
        return render(request, 'accounts/login.html', context)




@login_required(login_url='login')
def logout(request, *args, **kwargs):
    note = request.GET.get('note')
    cache.clear()
    auth.logout(request)
    return redirect('login')

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user=None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! Your account is now active. Please Login below.')
        messages.warning(request, 'Your email [ ' + str(user) + ' ]')
        return redirect('login')
    else:
        messages.warning(request, 'Invalid activation link')
        return redirect('register')

def forgotPasswordResetValidate(request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = Account._default_manager.get(pk=uid)
        except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
            user=None

        if user is not None and default_token_generator.check_token(user, token):
            request.session['uid'] = uid
            messages.success(request, 'Please reset your password')
            return redirect('forgotPasswordReset_page')
        else:
            messages.warning(request, 'This link has been expired')
            return redirect('login')

def forgotPasswordReset_page(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset successful, login below.')
            return redirect('login')
        else:
            messages.warning(request, 'Password do not match.')
            return redirect('forgotPasswordReset_page')
    else:
        return render(request, 'accounts/forgotPasswordReset_page.html')

@login_required(login_url = 'login')
def dashboard(request, *args, **kwargs):
    current_user = request.user
    group = current_user.group.name
    authorised=False
    if current_user.is_authenticated and group == "Seller":
        authorised =True
    if current_user.is_admin or current_user.is_superadmin:
        order = OrderProduct.objects.filter(~Q(is_deleted=True), ordered=True)

        order_filter = OrderProductFilter(request.GET, queryset=order)
        order = order_filter.qs #for status queryset

        total_amount = 0
        for item in order:
            total_amount+=item.total_price

        count = order.count()

        sent = OrderProduct.objects.filter(status='Sent', ordered=True)
        sent_count=sent.count()
        pending = OrderProduct.objects.filter(status='Pending', ordered=True)
        pending_count = pending.count()
        cancel = OrderProduct.objects.filter(status='Cancelled', ordered=True)
        cancel_count = cancel.count()
        for_payment = OrderProduct.objects.filter(for_payment=True, ordered=True)
        for_payment_count = for_payment.count()

    else:
        order=OrderProduct.objects.filter(cus_item_delete=False, user=current_user, ordered=True, cus_ref_accept_del=False).order_by('-updated_at')

        status = request.GET.get('status')
        if status != None:
            order = order.filter(status=status)
        else:
            pass

        count = order.count()
        sent = OrderProduct.objects.filter(user=current_user, status='Sent', ordered=True)
        sent_count=sent.count()
        pending = OrderProduct.objects.filter(user=current_user, status='Pending', ordered=True)
        pending_count = pending.count()
        cancel = OrderProduct.objects.filter(user=current_user, status='Cancelled', ordered=True)
        cancel_count = cancel.count()
        for_payment_count = ''
        order_filter=''
        total_amount = ''

    context = {'orders':order, 'count':count,'pending':pending_count,'cancel':cancel_count,'sent':sent_count, 'authorised':authorised, 'for_payment_count': for_payment_count, 'order_filter':order_filter, 'total_amount':total_amount}
    return render(request, 'accounts/dashboard.html', context)

@login_required(login_url = 'login')
@allowed_users(allowed_roles=['admin'])
def dashboard_single(request):
    current_user = request.user
    group = current_user.group.name
    authorised=False
    if current_user.is_authenticated and group == "Seller":
        authorised =True
    if current_user.is_admin or current_user.is_superadmin:
        orderproducts = OrderProduct.objects.filter(Q(ordered=True, is_deleted=True) | Q(status='Cancelled')).order_by('-updated_at')

        count = orderproducts.count()
        sent_count=''
        pending_count = ''
        cancel = OrderProduct.objects.filter(status='Cancelled', ordered=True)
        cancel_count = cancel.count()

    else:
        orderproducts = OrderProduct.objects.filter(user=current_user, ordered=True).order_by('-updated_at')
        count = orderproducts.count()
        sent = OrderProduct.objects.filter(user=current_user, status='Sent', ordered=True)
        sent_count=sent.count()
        pending = OrderProduct.objects.filter(user=current_user, status='Pending', ordered=True)
        pending_count = pending.count()
        cancel = OrderProduct.objects.filter(user=current_user, status='Cancelled',ordered=True)
        cancel_count = cancel.count()

    context = {'orderproducts':orderproducts, 'count':count,'pending':pending_count,'cancel':cancel_count,'sent':sent_count}
    return render(request, 'accounts/dashboard_single.html', context)



@login_required(login_url = 'login')
@allowed_users(allowed_roles=['Seller'])
def my_store_order(request, *args, **kwargs):
    current_user = request.user
    group = current_user.group.name
    authorised=False
    if current_user.is_authenticated and group == "Seller":
        authorised =True

        order = OrderProduct.objects.filter(~Q(is_deleted=True), product__added_by=current_user, ordered=True).order_by('updated_at')

        order_list_days = []
        for item in order:
            first_date = item.updated_at
            delta = datetime.datetime.today().replace(tzinfo=None)-first_date.replace(tzinfo=None)
            days_dif = delta.days
            if days_dif >=0:
                order_list_days.append(item.order.order_number)

        order_filter = OrderProductFilterSeller(request.GET, queryset=order)
        order = order_filter.qs

        total_amount = 0
        for item in order:
            total_amount+=item.total_price

        count = order.count()

        sent = OrderProduct.objects.filter(product__added_by=current_user, status='Sent', ordered=True)
        sent_count=sent.count()
        pending = OrderProduct.objects.filter(product__added_by=current_user, status='Pending', ordered=True)
        pending_count = pending.count()
        cancel = OrderProduct.objects.filter(product__added_by=current_user, status='Cancelled', ordered=True)
        cancel_count = cancel.count()
        for_payment = OrderProduct.objects.filter(for_payment=True, ordered=True)
        for_payment_count = for_payment.count()

    else:
        messages.warning(request, 'Access not permitted!')
        return redirect('store')

    context = {'orders':order, 'count':count,'pending':pending_count,'cancel':cancel_count,'sent':sent_count, 'authorised':authorised, 'order_filter':order_filter, 'for_payment_count': for_payment_count, 'order_list_days':order_list_days, 'total_amount':total_amount}
    return render(request, 'accounts/my_store_order.html', context)



def forgotPassword(request):
    if request.method == 'POST':
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            current_site = get_current_site(request)
            mail_subject = 'Reset Password'
            message = render_to_string('accounts/forgotPassword_verification_email.html', {
                'user':user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email = email
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            return redirect('/accounts/login?command=pwdvalidation&email='+email)
        else:
            messages.warning(request, 'Account does not exists.')
            return redirect('forgotPassword')

    return render(request, 'accounts/forgotPassword.html')

@login_required(login_url = 'login')
def my_profile(request):
    info = Account.objects.get(email=request.user)
    context = {'info': info}
    return render(request, 'accounts/my_profile.html', context)


def save_temp_profile_image_from_base64String(imageString, user):
    INCORRECT_PADDING_EXCEPTION = "Incorrect padding"
    try:
        if not os.path.exists(settings.TEMP):
            os.mkdir(settings.TEMP)
        if not os.path.exists(settings.TEMP + "/" + str(user.pk)):
            os.mkdir(settings.TEMP + "/" + str(user.pk))
        url = os.path.join(settings.TEMP + "/" + str(user.pk),TEMP_PROFILE_IMAGE_NAME)
        storage = FileSystemStorage(location=url)
        image = base64.b64decode(imageString)
        with storage.open('', 'wb+') as destination:
            destination.write(image)
            return url
    except Exception as e:
        print("exception: " + str(e))

        if str(e) == INCORRECT_PADDING_EXCEPTION:
            imageString += "=" * ((4 - len(imageString) % 4) % 4)
            return save_temp_profile_image_from_base64String(imageString, user)
    return None


def crop_image(request, *args, **kwargs):
    payload = {}
    user = request.user
    if request.POST and user.is_authenticated:
        try:
            imageString = request.POST.get("image")
            url = save_temp_profile_image_from_base64String(imageString, user)
            img = cv2.imread(url)

            cropX = int(float(str(request.POST.get("cropX"))))
            cropY = int(float(str(request.POST.get("cropY"))))
            cropWidth = int(float(str(request.POST.get("cropWidth"))))
            cropHeight = int(float(str(request.POST.get("cropHeight"))))
            if cropX < 0:
                cropX = 0
            if cropY < 0:
                cropY = 0
            crop_img = img[cropY:cropY+cropHeight, cropX:cropX+cropWidth]
            cv2.imwrite(url, crop_img)

            user.profile_pic.delete()

            user.profile_pic.save("profile_image.png", files.File(open(url, 'rb')))
            user.save()
            os.remove(url)
            payload['result'] = "success"
            # payload['cropped_profile_image'] = user.profile_pic.url
            # delete temp file
        except Exception as e:
            print("exception: " + str(e))
            payload['result'] = "error"
            payload['exception'] = str(e)
    return HttpResponse(json.dumps(payload), content_type="application/json")


@login_required(login_url = 'login')
def edit_profile(request):
    accounts = Account.objects.get(email=request.user)
    user_country = accounts.country
    if request.method == 'POST':

        form = EditProfileForm(request.POST, instance=accounts)
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.phone_number = form.cleaned_data['phone']
            user.profession = form.cleaned_data['profession']
            user.address_line_1 = form.cleaned_data['address_line_1']
            user.address_line_2 = form.cleaned_data['address_line_2']
            user.country = form.cleaned_data['country']
            user.state = form.cleaned_data['state']
            user.city = form.cleaned_data['city']
            user.zip = form.cleaned_data['zip']
            user.save()
            messages.success(request, 'Your profile has been successfully updated.')
            return redirect('edit_profile')
    else:
        form = EditProfileForm(instance=accounts)

    context={'form':form, 'accounts':accounts, 'user_country':user_country}
    context['DATA_UPLOAD_MAX_MEMORY_SIZE'] = settings.DATA_UPLOAD_MAX_MEMORY_SIZE
    return render(request, 'accounts/edit_profile.html', context)


@login_required(login_url = 'login')
def change_password(request):
     accounts = Account.objects.get(email=request.user)
     if request.method == 'POST':
         current_password = request.POST['old_password']
         new_password = request.POST['new_password2']
         form = PwdChangeForm(request.POST, instance=accounts)
         if form.is_valid():
            success = accounts.check_password(current_password)
            if success:
                 accounts.set_password(new_password)
                 accounts.save()
                 messages.success(request, 'Login with your new password.')
                 return redirect('login')
            else:
                messages.warning(request, 'Password update Fail! You provided a wrong Old Password.')
                return redirect('change_password')
     else:
         form = PwdChangeForm(instance=accounts)
     context = {'accounts':accounts, 'form':form}
     return render(request, 'accounts/change_password.html', context)



def account_view(request, *args, **kwargs):
    """
    - Logic here is kind of tricky
    is_self
    is_friend
    	-1: NO_REQUEST_SENT
    	0: THEM_SENT_TO_YOU
    	1: YOU_SENT_TO_THEM
    """

    context = {}

    user_id = kwargs.get("user_id")
    try:
        account = Account.objects.get(pk=user_id)
    except:
        return HttpResponse("Something went wrong.")

    if account:
        context['id'] = account.id
        context['username'] = account.username
        context['email'] = account.email
        context['profile_pic'] = account.profile_pic.url
        context['hide_email'] = account.hide_email

        try:
        	friend_list = FriendList.objects.get(user=account)
        except FriendList.DoesNotExist:
        	friend_list = FriendList(user=account)
        	friend_list.save()
        friends = friend_list.friends.all()
        context['friends'] = friends

        # Define template variables
        is_self = True
        is_friend = False
        request_sent = FriendRequestStatus.NO_REQUEST_SENT.value # range: ENUM -> friend/friend_request_status.FriendRequestStatus
        friend_requests = None
        user = request.user
        if user.is_authenticated and user != account:
        	is_self = False
        	if friends.filter(pk=user.id):
        		is_friend = True
        	else:
        		is_friend = False
        		# CASE1: Request has been sent from THEM to YOU: FriendRequestStatus.THEM_SENT_TO_YOU
        		if get_friend_request_or_false(sender=account, receiver=user) != False:
        			request_sent = FriendRequestStatus.THEM_SENT_TO_YOU.value
        			context['pending_friend_request_id'] = get_friend_request_or_false(sender=account, receiver=user).id
        		# CASE2: Request has been sent from YOU to THEM: FriendRequestStatus.YOU_SENT_TO_THEM
        		elif get_friend_request_or_false(sender=user, receiver=account) != False:
        			request_sent = FriendRequestStatus.YOU_SENT_TO_THEM.value
        		# CASE3: No request sent from YOU or THEM: FriendRequestStatus.NO_REQUEST_SENT
        		else:
        			request_sent = FriendRequestStatus.NO_REQUEST_SENT.value

        elif not user.is_authenticated:
        	is_self = False
        else:
        	try:
        		friend_requests = FriendRequest.objects.filter(receiver=user, is_active=True)
        	except:
        		pass

        # Set the template variables to the values
        context['is_self'] = is_self
        context['is_friend'] = is_friend
        context['request_sent'] = request_sent
        context['friend_requests'] = friend_requests
        context['BASE_URL'] = settings.BASE_URL
        return render(request, "accounts/account.html", context)
