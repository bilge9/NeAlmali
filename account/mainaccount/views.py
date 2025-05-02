from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect
from .models import Product, Category

def index(request):
    return render(request, 'index.html')

@never_cache
def register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        print(f"Formdan gelen bilgiler: {full_name}, {email}, {password}")  # Debug
        if password != confirm_password:
            messages.error(request , 'Şifreler eşleşmiyor.')
            return redirect('register')
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'Bu e-posta adresiyle bir kullanıcı zaten var.')
            return redirect('register')
        
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        

        login(request, user)
        messages.success(request, 'Başarıyla kaydoldunuz.')
        return redirect('index')

    return render(request, 'register.html')

@never_cache
def login_view(request):  # 'login' ismi Python'da gömülü olduğu için '_view' ekledik
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Başarıyla giriş yaptınız.')
            return redirect('index')
        else:
            messages.error(request, 'Geçersiz e-posta veya şifre.')
            return redirect('login_view')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)  
    messages.success(request, "Başarıyla çıkış yaptınız!")  
    return redirect('index')



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

def forum(request):
    return render(request, 'forum.html')

def forum_caption(request):
    return render(request, 'forum_caption.html')

def product_info(request):
    return render(request, 'product_info.html')
