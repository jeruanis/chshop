from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, ProductGallery
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from django.core.paginator import Paginator, EmptyPage, InvalidPage, PageNotAnInteger
from django.db.models import Q
from .forms import ReviewForm, ContactForm, UpdateProductForm, ProductImageForm, GalleryImageForm, CreateVariationForm
from .models import ReviewRating, Variation
from django.contrib import messages
from orders.models import OrderProduct
from .filter import ProductPriceFilter
from accounts.models import Account

from django.core.mail import send_mail, BadHeaderError, EmailMessage
from shopme.settings import EMAIL_HOST_USER
from django.template.loader import render_to_string

from django.forms import modelformset_factory
from django import forms

from django.http import HttpResponse, JsonResponse
import json
from django.contrib.auth.decorators import login_required

from rest_framework import generics
from .serializers import ProductSerializer
from rest_framework import permissions
from .permission import IsOwnerOrReadOnly

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.authtoken.views import obtain_auth_token

from rest_framework.authtoken.models import Token
from rest_framework.decorators import APIView

from rest_framework.pagination import LimitOffsetPagination
from rest_framework import status

from django.views.decorators.cache import cache_page


class ProductsPostList(generics.ListAPIView):
    queryset = Product.objects.all().order_by('created_date')
    serializer_class = ProductSerializer

class ProductDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly
    ]

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'api_products_view': reverse('api_products_view', request=request, format=format),
    })

class ProductList(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('created_date')
    serializer_class = ProductSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly
    ]

    def perform_create(self, serializer):
        serializer.save(added_by=self.request.user)

def error_404(request, exception):
    context = {}
    return render(request, 'errors/error_404.html', context)

def error_400(request, exception):
    context = {}
    return render(request, 'errors/error_400.html', context)

def error_500(request):
    context = {}
    return render(request, 'errors/error_500.html', context)

def prodVariation(request, pk):
    if request.user.is_authenticated:
        user = Account.objects.get(email=request.user.email)
        product = Product.objects.get(pk=pk)
        variation_form = CreateVariationForm()
        if product.added_by == user:
            if request.method == 'POST':
                variation_form = CreateVariationForm(request.POST)
                try:
                    if variation_form.is_valid():
                        prod = variation_form.cleaned_data['product']
                        variation_category = variation_form.cleaned_data['variation_category']
                        variation_value = variation_form.cleaned_data['variation_value']
                        try:
                            is_variation_existing = Variation.objects.filter(product__id=pk, variation_category=variation_category, variation_value=variation_value).exists()
                        except Exception as e:
                            message.warning(request, 'There was an error {}'.format(e))
                        if not is_variation_existing:
                            new_variation = Variation.objects.create(product=product, variation_category=variation_category, variation_value=variation_value)
                            new_variation.save()
                        else:
                            messages.warning(request, 'The variation you are trying to add exists')
                    else:
                        size = request.POST.get('size')
                        color = request.POST.get('color')
                        try:
                            if size:
                                variation = Variation.objects.filter(product__id=pk, variation_category='size', variation_value=size)
                                variation.delete()
                            if color:
                                variation = Variation.objects.filter(product__id=pk, variation_category='color', variation_value=color)
                                variation.delete()
                        except Exception as e:
                            messages.warning(request, 'There was a problem {}'.format(e))
                except Exception as e:
                    pass

        context ={'prod_id':pk, 'form':CreateVariationForm, 'product':product}
        return render(request, 'store/add_delete_variation.html', context)
    else:
        message.warning(request, 'Permission not allowed')
        return redirect('store')

def liveSearch(request, *args, **kwargs):
    keyword = request.GET.get('keyword')
    if keyword != '':
        products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))[:6]
        if request.is_ajax():
            html=render_to_string(
               template_name = "includes/ajax_search.html",
               context = {'products':products}
            )
            data_dict = {"html_from_view": html}
        return JsonResponse(data=data_dict, safe=False)

@login_required(login_url='login')
def delete_product(request, product_slug):
    if request.user.is_authenticated:
        user = Account.objects.get(email=request.user.email)
        product = Product.objects.get(slug=product_slug)
        added_by = product.added_by
        group = user.group
        if user == added_by and group.name == 'Seller':
            product.delete()
            messages.success(request, 'Product deleted successfully!')
        else:
            messages.warning(request, 'Access not permitted!')

        return redirect('store')
    else:
        messages.warning(request, 'Access not permitted!')
        return redirect('store')


@login_required(login_url='login')
def add_product(request):
    if request.user.is_authenticated:
        user = Account.objects.get(email=request.user.email)
        store = user.username
        seller_name = store
        galleryFormSet = modelformset_factory(ProductGallery, form=GalleryImageForm, fields=('image',), extra=1, can_delete=True)
        group = user.group

        groupB = 'Seller'
        if group.name == 'Seller':
            if request.method == 'POST':
                postForm = UpdateProductForm(request.POST)
                gpformset = galleryFormSet(request.POST, request.FILES, queryset=Product.objects.none())
                productImage = ProductImageForm(request.POST, request.FILES)
                if(postForm.is_valid() and gpformset.is_valid() and productImage.is_valid()):
                    instances = gpformset.save(commit=False)
                    for obj in gpformset.deleted_objects:
                        obj.delete()

                    product_name = postForm.cleaned_data['product_name']
                    description = postForm.cleaned_data['description']
                    price = postForm.cleaned_data['price']
                    stock = postForm.cleaned_data['stock']
                    category = postForm.cleaned_data['category']
                    is_digital = postForm.cleaned_data['is_digital']

                    prod = Product.objects.create(
                        added_by = user,
                        product_name = product_name,
                        description = description,
                        price = price,
                        stock = stock,
                        category = Category.objects.get(category_name=category),
                        is_digital = is_digital
                    )
                    prod.save()

                    product = Product.objects.get(id=prod.id)
                    product.images = productImage.cleaned_data['images']
                    product.save()

                    for instance in instances:
                        instance.product = product
                        instance.image = instance.image
                        instance.save()

                    messages.success(request, 'Product added successfully!')
                    return redirect('add_product')
                else:
                    print(postForm.errors, gpformset.errors)
                    messages.warning(request, 'There was an error during product add!'+ str(postForm.errors))

            else:
                postForm = UpdateProductForm()
                gpformset = galleryFormSet(queryset=Product.objects.none())
                productImage = ProductImageForm()
        else:
            messages.warning(request, 'Access not permitted!')
            return redirect('store')
    else:
        messages.warning(request, 'Access not permitted!')
        return redirect('store')

    context = {'info':seller_name, 'form':postForm, 'productImage':productImage, 'formset':gpformset}
    return render(request, 'store/add_product.html', context)


@login_required(login_url='login')
def update_product(request, product_slug):
    if request.user.is_authenticated:
        user = Account.objects.get(email=request.user.email)
        product = Product.objects.get(slug=product_slug)
        prod_ow = product.added_by
        group = user.group

        if user == prod_ow and group.name == 'Seller':
            if user == prod_ow:
                owner = True
            else:
                owner = False
            existing_product = Product.objects.get(slug=product_slug)
            existing_images = ProductGallery.objects.filter(product = existing_product)
            galleryFormSet = modelformset_factory(ProductGallery, form=GalleryImageForm, fields=('image',), extra=1, can_delete=True)
            postForm = UpdateProductForm(instance = existing_product)
            seller_name = existing_product.added_by.username
            category_slug = existing_product.category

            if request.method == 'POST':
                gformset = galleryFormSet(request.POST, request.FILES, queryset=existing_images)
                productImage = ProductImageForm(request.POST, request.FILES, instance = existing_product)
                postForm = UpdateProductForm(request.POST, instance=existing_product)

                print([form.cleaned_data for form in gformset.deleted_forms])

                if(postForm.has_changed() | productImage.has_changed() | gformset.has_changed()):
                    if postForm.is_valid() and productImage.is_valid() and gformset.is_valid():
                        instances = gformset.save(commit=False)

                        for obj in gformset.deleted_objects:
                            obj.delete()

                        for instance in instances:
                            instance.product=existing_product
                            instance.image=instance.image
                            instance.save()

                        productImage.save()
                        prod = postForm.save(commit=False)
                        prod.product_name = postForm.cleaned_data['product_name']
                        prod.description = postForm.cleaned_data['description']
                        prod.price = postForm.cleaned_data['price']
                        prod.stock = postForm.cleaned_data['stock']
                        prod.category = postForm.cleaned_data['category']
                        prod.is_digital = postForm.cleaned_data['is_digital']
                        prod.save()

                        messages.success(request, 'Update successfully!')
                        return redirect('/store/category/'+ str(prod.category.slug) +'/'+ str(prod.slug)+'/')
                    else:
                        print(postForm.errors, gformset.errors)
                        messages.warning(request, 'There was an error during update!'+ str(postForm.errors))
                else:
                    messages.warning(request, 'Nothing has changed!')
                    return redirect('/store/category/'+ str(category_slug) +'/'+ str(product_slug)+'/')
            else:
                gformset = galleryFormSet(queryset=existing_images)
                productImage = ProductImageForm(instance = existing_product)
        else:
            messages.warning(request, 'Permision denied!')
            return redirect('store')
    else:
        messages.warning(request, 'Access not permitted!')
        return redirect('store')

    context = {'info':seller_name, 'form':postForm, 'product_info':existing_product, 'productImage':productImage, 'formset':gformset, 'owner':owner, 'product_slug':product.slug}
    return render(request, 'store/update_product.html', context)


def pagination(request, value):
    page = request.GET.get('page', 1)
    paginator = value
    try:
        paged_products = paginator.page(page)
    except PageNotAnInteger:
        paged_products = paginator.page(1)
    except EmptyPage:
        paged_products = paginator.page(paginator.num_pages)
    return paged_products


# @cache_page(60 * 5)
def my_store(request, seller):
    try:
        user = Account.objects.get(username = seller)
        products = Product.objects.filter(added_by=user)
        paged_products=pagination(request, Paginator(products, 6))
        context = {'products':paged_products, 'info':user}
        return render(request, 'store/my_store.html', context)
    except Account.DoesNotExist:
        messages.warning(request, 'Store does not exist!')
        return redirect('store')


# @cache_page(60 * 5)
def store(request, category_slug=None):
    if request.user.is_authenticated:
        user = request.user
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category = categories, is_available=True).order_by('-modified_date')

        paged_products=pagination(request, Paginator(products, 5))

        product_count = products.count()
        context = {'products':paged_products, 'product_count': product_count}
        return render(request, 'store/search_result.html', context)

    else:
        products = Product.objects.all().filter(is_available = True).order_by('-modified_date')

        paged_products=pagination(request, Paginator(products, 5))

        context = {'products':paged_products}
        return render(request, 'store/store.html', context)


def product_detail(request, category_slug, product_slug):
    product = Product.objects.get(slug=product_slug)
    prod_ow = product.added_by
    owner = False
    category = get_object_or_404(Category, slug=category_slug)
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)

        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()

        in_cart_user = None
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        user = Account.objects.get(email=request.user.email)
        if user == prod_ow:
            owner = True
        else:
            owner = False

        in_cart_user = CartItem.objects.filter(user=request.user, product=single_product).exists()

        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    variation_option = ['colors', 'sizes']

    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    context={'single_product': single_product, 'in_cart':in_cart, 'in_cart_user':in_cart_user, 'orderproduct':orderproduct, 'reviews':reviews, 'images':product_gallery, 'category':category, 'owner':owner, 'p_owner':prod_ow, 'variation_option':variation_option}
    return render(request, 'store/product_detail.html', context)


# @cache_page(60 * 5)
def search(request, *args, **kwargs):
    keyword = request.GET.get('keyword')
    if keyword != '':
        products = Product.objects.order_by('-created_date').filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
        product_count= products.count()
        context = {'products': products, 'product_count':product_count ,'keyword':keyword}
        return render(request, 'store/search_result.html', context)
    else:
        return redirect('store')


# @cache_page(60 * 5)
def price_search(request):
    products = Product.objects.all().filter(is_available = True).order_by('modified_date')
    if 'min' in request.GET or 'max' in request.GET:
        min= request.GET['min']
        max= request.GET['max']
    if min or max:
        my_filter = ProductPriceFilter(request.GET, queryset=products)
        products = my_filter.qs
        product_count= products.count()

        paged_products=pagination(request, Paginator(products, 5))

    else:
        my_filter = ProductPriceFilter()
        product_count= products.count()

        paged_products=pagination(request, Paginator(products, 5))

    context = {'products':paged_products, 'product_count': product_count}
    return render(request, 'store/search_result.html', context)


@login_required(login_url='login')
def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    user = Account.objects.get(email=request.user)
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.') #updated not created
            return redirect(url)
        except(ReviewRating.DoesNotExist, ValueError):
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)
            else:
                messages.warning(request, 'There was an error. Have you chosen star rating?')
                return redirect(url)


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email_address']
            subject = "jv-store Client inquiry"
            message = render_to_string("store/contact_us_email.html", {
            'first_name': form.cleaned_data['first_name'],
            'email': form.cleaned_data['email_address'],
            'message':form.cleaned_data['message']
            })

            try:
                send_email = EmailMessage(subject, message, email, [EMAIL_HOST_USER] )
                send_email.send()
            except BadHeaderError:
                return HttpResponse('Invalid header found.')
            messages.success(request, 'Your message was sent successfully!')
            return redirect ("store")

    form = ContactForm()
    return render(request, "store/contact.html", {'form':form})
