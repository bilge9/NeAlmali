from django.shortcuts import render
from .models import Product, Category

def index(request):
    return render(request, 'index.html')

def register(request):
    return render(request, 'register.html')

def login_view(request):  # 'login' ismi Python'da gömülü olduğu için '_view' ekledik
    return render(request, 'login.html')

def shopping(request):
    return render(request, 'shopping.html')

def shop_categories(request):
    return render(request, 'shop_categories.html')
# Create your views here.

def product_list(request):
    color_filter = request.GET.get('color')
    category_id = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    products = Product.objects.all()
    category_name = None

    if category_id:
        products = products.filter(category_id=category_id)
        category = Category.objects.filter(id=category_id).first()
        if category:
            category_name = category.name
    
    if color_filter:
        products =products.filter(color=color_filter)

    if min_price:
        products = products.filter(price__gte=min_price) # price__gte means price greater than or equal to min_price
    
    if max_price:
        products = products.filter(price__lte=max_price) # price__lte means price less than or equal to max_price

    context = {
        'products': products,
        'categories': Category.objects.all(),
        'category_name': category_name,
        'selected_color': color_filter,
        'min_price': min_price,
        'max_price': max_price,
    }
    return render(request, 'shopping.html', context)