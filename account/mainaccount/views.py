from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, ForumCategory, Thread, Reply, ThreadVote, Cart, CartItem, Favorite
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from .forms import ProductReviewForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings

def index(request):
    return render(request, 'index.html')

@never_cache
def register(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        next_page = request.POST.get('next') or 'index'  # fallback to index if boş

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
        return redirect(next_page)

    return render(request, 'register.html')

@never_cache
def login_view(request):  # 'login' ismi Python'da gömülü olduğu için '_view' ekledik
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        next_page = request.POST.get('next') or 'index'  # fallback to index if boş

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Başarıyla giriş yaptınız.')
            return redirect(next_page)
        else:
            messages.error(request, 'Geçersiz e-posta veya şifre.')
            return redirect('login_view')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)  
    messages.success(request, "Başarıyla çıkış yaptınız!")  
    return redirect('index')



def shopping(request):
    categories = Category.objects.all()  # Tüm kategorileri al

    return render(request, 'shopping.html', {
        'categories': categories
    })

def shop_categories(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    # Seçilen kategori ve alt kategorilerini al
    categories = category.get_descendants(include_self=True)
    
    # Bu kategorilere ait ürünleri getir
    products = Product.objects.filter(category__in=categories).prefetch_related('images').distinct()

    # Sol menüde göstermek için yalnızca birinci seviyedeki alt kategorileri al
    subcategories = category.get_children()

    # Eğer kategori birinci seviye değilse, üst kategoriyi al
    if category.parent:
        parent_category = category.parent
    else:
        parent_category = None

    # Tüm kategorileri al (Üst kategoriler de dahil)
    all_categories = Category.objects.all()

    return render(request, 'shop_categories.html', {
        'category': category,
        'products': products,
        'subcategories': subcategories,  # Sol menü için
        'categories': categories,  # Üst kategori için
        'parent_category': parent_category,  # Üst kategori için
        'all_categories': all_categories,  # Tüm kategoriler için
    })

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

def user_has_purchased(user, product):
    # Sipariş sistemi varsa buraya kontrol eklenmeli
    return True  # Şimdilik herkes yorum yapabilir gibi düşünelim

def product_info(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()
    form = None

    # Yorum yapabilmek için kullanıcı doğrulaması ve ürünü satın almış olma kontrolü
    if request.user.is_authenticated and user_has_purchased(request.user, product):
        if request.method == 'POST':
            form = ProductReviewForm(request.POST)
            if form.is_valid():
                # Yorum kaydetme işlemi
                review = form.save(commit=False)
                review.product = product
                review.user = request.user
                review.save()
                
                # Başarı mesajı ekleyelim
                messages.success(request, 'Yorumunuz başarıyla gönderildi!')
                
                # Yorum yapıldıktan sonra sayfayı yenileyip formu sıfırlıyoruz
                return redirect('product_info', product_id=product.id)
        else:
            form = ProductReviewForm()  # İlk sayfa yüklenirken boş formu gönder

    return render(request, 'product_info.html', {
        'product': product,
        'form': form,
        'reviews': reviews
    })

# Forum Kısmı
def forum_page(request):
    categories = ForumCategory.objects.all()
    threads = Thread.objects.all().order_by('-id')

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect('/giris-yap/?next=' + request.path)

        title = request.POST.get("title")
        content = request.POST.get("content")
        category_ids = request.POST.getlist("categories")

        if title and content and category_ids:
            thread = Thread.objects.create(
                title=title,
                content=content,
                user=request.user
            )
            thread.categories.set(category_ids)
            thread.save()
            return redirect("forum_page")

    return render(request, "forum.html", {
        "categories": categories,
        "threads": threads,
    })

def thread_detail(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)
     # Görüntülenme sayısını artır
    thread.views += 1
    thread.save(update_fields=['views'])
    replies = Reply.objects.filter(thread=thread).order_by('created_at')
   
      # Kategoriyi alıyoruz
    category_id = request.GET.get('category_id', None)  # URL'den category_id parametresini alıyoruz


    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Yanıt yazmak için giriş yapmalısınız.")

        content = request.POST.get('content')
        if content:
            Reply.objects.create(
                thread=thread,
                user=request.user,
                content=content
            )
            return redirect('thread_detail', thread_id=thread_id)

    return render(request, 'thread_detail.html', {
        'thread': thread,
        'replies': replies,
        'category_id': category_id  
    })
    
def reply_create(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id)

    if request.method == 'POST':
        content = request.POST.get('content')
        if content and request.user.is_authenticated:
            Reply.objects.create(
                thread=thread,
                user=request.user,
                content=content
            )
    return redirect('thread_detail', thread_id=thread.id)

def vote_thread(request, thread_id, vote_type):
    thread = get_object_or_404(Thread, id=thread_id)
    
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Beğenme işlemi için giriş yapmalısınız.")    
    
    user = request.user
    if vote_type not in ['like', 'dislike']:
        return redirect('thread_detail', thread_id=thread.id)

    # Var olan oy kontrolü
    existing_vote = ThreadVote.objects.filter(user=user, thread=thread).first()

    if existing_vote:
        if existing_vote.value == vote_type:
            # Aynı oyu tekrar verdiyse: oyunu geri çekmek istiyor demektir
            existing_vote.delete()
        else:
            # Oy türünü değiştiriyor
            existing_vote.value = vote_type
            existing_vote.save()
    else:
        # İlk kez oy veriyor
        ThreadVote.objects.create(user=user, thread=thread, value=vote_type)

    return redirect('thread_detail', thread_id=thread.id)

def category_detail(request, category_id):
    category = get_object_or_404(ForumCategory, id=category_id)
    threads = category.threads.all()  # Bu kısımda `threads` ilişkisini kullanabilirsiniz
    return render(request, 'category_detail.html', {'category': category, 'threads': threads})

def category_list(request):
    categories = ForumCategory.objects.all()  # Tüm kategorileri al
    return render(request, 'category_list.html', {'categories': categories})

def category_threads(request, category_id):
    category = get_object_or_404(ForumCategory, id=category_id)
    threads = Thread.objects.filter(categories=category).order_by('-created_at')
    return render(request, 'category_threads.html', {
        'category': category,
        'threads': threads
    })

#Sepetim sayfası

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    # sepette bu ürün zaten varsa, adedini artır
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart_detail')  # sepet sayfasına yönlendir

def cart_detail(request):
    cart = Cart.objects.get(user=request.user)
    items = cart.items.all()
    total = sum(item.get_total_price() for item in items)
    return render(request, 'cart_detail.html', {
        'items': items,
        'total': total
    })

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)

    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()

    return redirect('cart_detail')  # sepete yönlendiriyoruz

#favoriler

@login_required
def add_to_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    Favorite.objects.get_or_create(user=request.user, product=product)
    return redirect('favorite_list')

@login_required
def favorite_list(request):
    favorites = Favorite.objects.filter(user=request.user)
    return render(request, 'favorite_list.html', {'favorites': favorites})