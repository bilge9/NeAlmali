from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Attribute, ProductAttributeValue, ProductImage, SellerProfile,  Category, ForumCategory, Thread, Reply, ThreadVote, Cart, CartItem, Favorite
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from .forms import ProductReviewForm, ProductForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.db.models import Q
from django.core.paginator import Paginator
import re
from django.db.models import Q

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
        is_seller = request.POST.get('is_seller') == 'on'

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
        
        # ✅ Satıcı ise SellerProfile oluştur
        if is_seller:
            from .models import SellerProfile
            SellerProfile.objects.create(
                user=user,
                store_name=f"{full_name} Store",  # Basit bir varsayılan değer
                is_approved=False  # Admin onaylamalı
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
    highlighted_categories = Category.objects.filter(highlighted=True)
    products = Product.objects.all()

    return render(request, 'shopping.html', {
        'categories': categories,
        'highlighted_categories': highlighted_categories,
        'products': products
    })


def shop_categories(request, category_id):
    category = get_object_or_404(Category, id=category_id)

    # Seçilen kategori ve alt kategorilerini al
    categories = category.get_descendants(include_self=True)

    # Arama sorgusunu al
    query = request.GET.get('q')

    # Arama varsa filtrele
    if query:
        # İlk olarak Product modelindeki doğrudan alanlarda arama
        base_filter = Q(name__icontains=query) | Q(description__icontains=query) | Q(brand__icontains=query) | Q(category__name__icontains=query)

        # Ardından ilgili attribute_value tablosunda arama yapalım
        product_ids_from_attributes = ProductAttributeValue.objects.filter(
            value__icontains=query
        ).values_list('product_id', flat=True)

        # Tüm ürünleri birleştirelim (doğrudan eşleşen + attribute ile eşleşen)
        products = Product.objects.filter(
            Q(category__in=categories) & (base_filter | Q(id__in=product_ids_from_attributes))
        ).prefetch_related('images', 'attribute_values__attribute').distinct()
    else:
        products = Product.objects.filter(
            category__in=categories
        ).prefetch_related('images', 'attribute_values__attribute').distinct()

    subcategories = category.get_children()

    parent_category = category.parent if category.parent else None

    all_categories = Category.objects.all()

    return render(request, 'shop_categories.html', {
        'category': category,
        'products': products,
        'subcategories': subcategories,
        'categories': categories,
        'parent_category': parent_category,
        'all_categories': all_categories,
        'query': query,  # Arama kutusunda geri göstermek için
    })


def user_has_purchased(user, product):
    # Sipariş sistemi varsa buraya kontrol eklenmeli
    return True  # Şimdilik herkes yorum yapabilir gibi düşünelim

def product_info(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = product.reviews.all()
    form = None
    has_reviewed = False
    user_purchased = False

    # Yorum yapabilmek için kullanıcı doğrulaması ve ürünü satın almış olma kontrolü
    if request.user.is_authenticated:
        user_purchased = user_has_purchased(request.user, product)
        has_reviewed = reviews.filter(user=request.user).exists()

        if user_purchased and not has_reviewed:
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
        'reviews': reviews,
        'has_reviewed': has_reviewed,
        'user_purchased': user_purchased,
    })

# Forum Kısmı
def forum_page(request):
    categories = ForumCategory.objects.all()
    query = request.GET.get('q')
    
    if query:
        thread_list = Thread.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(categories__name__icontains=query) |
            Q(replies__content__icontains=query)
        ).distinct().order_by('-id')
    else:
        thread_list = Thread.objects.all().order_by('-id')
    
    paginator = Paginator(thread_list, 10)  # Sayfa başına 10 başlık
    page_number = request.GET.get("page")
    threads = paginator.get_page(page_number)

    # Çoklu kategori filtresi
    category_filter = request.GET.getlist("category")
    sort_by = request.GET.get("sort")  # Yeni: sıralama parametresi

    threads = Thread.objects.all()
    if category_filter:
        threads = threads.filter(categories__id__in=category_filter).distinct()

    # Sıralama işlemi
    if sort_by == "views":
        threads = threads.order_by("-views")
    elif sort_by == "likes":
        threads = threads.order_by("-like_count")
    elif sort_by == "dislikes":
        threads = threads.order_by("-dislike_count")
    else:
        threads = threads.order_by("-id")  # Varsayılan: en yeni başlıklar
    

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
             # İlgili başlıkları bul ve ata
            related = find_related_threads(thread)
            thread.related_threads.set(related)
            for r in related:
                r.related_threads.add(thread)

            return redirect("forum_page")


    return render(request, "forum.html", {
        "categories": categories,
        "threads": threads,
        "query": query,
        "selected_categories": list(map(int, category_filter)) if category_filter else [],
        "sort_by": sort_by,  # Şablonda kullanılacak
    })

def forum_autocomplete(request):
    term = request.GET.get('term', '')
    titles = []

    if term:
        threads = Thread.objects.filter(title__icontains=term).values('id', 'title')[:5]
        results = list(threads)

    return JsonResponse(results, safe=False)


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
        return JsonResponse({'error': 'Giriş yapmalısınız.'}, status=403)

    user = request.user

    if vote_type not in ['like', 'dislike']:
        return JsonResponse({'error': 'Geçersiz oy türü.'}, status=400)

    existing_vote = ThreadVote.objects.filter(user=user, thread=thread).first()

    if existing_vote:
        if existing_vote.value == vote_type:
            existing_vote.delete()
        else:
            existing_vote.value = vote_type
            existing_vote.save()
    else:
        ThreadVote.objects.create(user=user, thread=thread, value=vote_type)

    thread.update_vote_counts()

    return JsonResponse({
        'like_count': thread.like_count,
        'dislike_count': thread.dislike_count
    })

def extract_keywords(text):#ilgili başlık bulma kısmındaki kelime arayan kodlar
    words = re.findall(r'\w+', text.lower())
    return [word for word in words if len(word) > 3]

def find_related_threads(thread, max_results=5):
    text = thread.title + " " + thread.content
    keywords = extract_keywords(text)

    query = Q()
    for word in keywords:
        query |= Q(title__icontains=word) | Q(content__icontains=word)

 # Sadece aynı kategoriye sahip başlıklar içinde ara
     # Sadece aynı kategorilerde olan başlıkları getir
    same_category_threads = Thread.objects.filter(categories__in=thread.categories.all()).exclude(id=thread.id).distinct()

    possible_matches = same_category_threads.filter(query)


    results = []
    for t in possible_matches:
        other_text = t.title + " " + t.content
        other_keywords = set(extract_keywords(other_text))
        match_score = len(set(keywords) & other_keywords)
        results.append((match_score, t))

    results.sort(reverse=True, key=lambda x: x[0])
    return [t for score, t in results[:max_results]]

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

@login_required
def update_cart_item(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'increase':
            item.quantity += 1
        elif action == 'decrease' and item.quantity > 1:
            item.quantity -= 1
        item.save()
    return redirect('cart_detail')

@login_required
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)

    if request.method == 'POST':
        item.delete()
    return redirect('cart_detail')


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

@login_required
def seller_profile(request):
    if request.method == 'POST':
        product_form = ProductForm(request.POST)
        if product_form.is_valid():
            product = product_form.save(commit=False)
            product.seller = request.user
            product.save()

            images = request.FILES.getlist('images')
            main_index = int(request.POST.get('main_image_index', 0))  # Formdan gelen ana görselin index'i

            for idx, img in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=img,
                    is_main=(idx == main_index)  # Sadece seçilen index ana görsel olur
                )

            names = request.POST.getlist('attributes_name')
            values = request.POST.getlist('attributes_value')
            for name, value in zip(names, values):
                if name.strip():
                    attr, _ = Attribute.objects.get_or_create(name=name.strip())
                    ProductAttributeValue.objects.create(product=product, attribute=attr, value=value.strip())

            return redirect('seller_profile')

    else:
        product_form = ProductForm()

    products = Product.objects.filter(seller=request.user)
    profile = SellerProfile.objects.get(user=request.user)

    return render(request, 'seller_profile.html', {
        'product_form': product_form,
        'products': products,
        'profile': profile,
    })