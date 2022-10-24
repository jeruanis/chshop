from django.shortcuts import render
from store.models import Product
from django.core.paginator import Paginator
from django.core.paginator import Paginator, EmptyPage, InvalidPage, PageNotAnInteger
from django.views.debug import 

def home(request):
    paged_products=''
    try:
        products = Product.objects.all().filter(is_available = True, sold__gte = 5).order_by('created_date')[:8]
        page = request.GET.get('page', 1)
        paginator = Paginator(products, 4)
        try:
            paged_products = paginator.page(page)
        except PageNotAnInteger:
            paged_products = paginator.page(1)
        except EmptyPage:
            paged_products = paginator.page(paginator.num_pages)
    except Exception as e:
        pass

    context = {'products':paged_products}
    return render(request, 'home.html', context)

def seller_doc(request):
    return render(request, 'docs/seller.html')

def services_doc(request):
    return render(request, 'docs/services.html')

def api_doc(request):
    return render(request, 'docs/endpoints.html')
