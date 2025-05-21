from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Attribute, ProductAttributeValue, ProductImage, SellerProfile,  Category, ForumCategory, Thread, Reply, ThreadVote, Report, UserPoint, Coupon, Cart, CartItem, Favorite, UserProfile, Order, OrderItem, ProductReview
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from .forms import ProductReviewForm, ProductForm
from django.utils.http import url_has_allowed_host_and_scheme
from django.conf import settings
from django.db.models import Q
from django.core.paginator import Paginator
import re
from django.db.models import Q
from django.urls import reverse
from datetime import datetime, timezone
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash

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

        # Kullanıcı profili oluştur
        UserProfile.objects.create(user=user)
        
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
        return redirect(index)

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
    is_favorited = False 
    
    # Session üzerinden seçilen ürün ID'lerini al (eğer session'da yoksa boş liste kullan)
    selected_ids = request.session.get('selected_product_ids', [])
    
  
    # Yorum yapabilmek için kullanıcı doğrulaması ve ürünü satın almış olma kontrolü
    if request.user.is_authenticated:
        user_purchased = user_has_purchased(request.user, product)
        has_reviewed = reviews.filter(user=request.user).exists()
        is_favorited = Favorite.objects.filter(user=request.user, product=product).exists()


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
        'is_favorited': is_favorited,
        "existing_ids": selected_ids,
        
    })
from django.core.paginator import Paginator
from django.contrib import messages
from django.db.models import Q

def forum_page(request):
    categories = ForumCategory.objects.all()
    products = Product.objects.all()

    # Arama sorgusu
    query = request.GET.get('q')

    # Session'dan önceden seçilmiş ürünleri al
    preselected_ids = request.session.get('selected_product_ids', [])
    selected_products = Product.objects.filter(id__in=preselected_ids)

    # Başlangıç thread queryset'i (arama varsa filtrele)
    thread_list = Thread.objects.filter(is_hidden=False)
    if query:
        thread_list = thread_list.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(categories__name__icontains=query) |
            Q(replies__content__icontains=query)
        ).distinct()

    # Kategori filtreleme
    category_filter = request.GET.getlist("category")
    if category_filter:
        thread_list = thread_list.filter(categories__id__in=category_filter).distinct()

    # Sıralama
    sort_by = request.GET.get("sort")
    if sort_by == "views":
        thread_list = thread_list.order_by("-views")
    elif sort_by == "likes":
        thread_list = thread_list.order_by("-like_count")
    elif sort_by == "dislikes":
        thread_list = thread_list.order_by("-dislike_count")
    else:
        thread_list = thread_list.order_by("-id")

    # Sayfalama
    paginator = Paginator(thread_list, 10)
    page_number = request.GET.get("page")
    threads = paginator.get_page(page_number)

    # POST ile başlık oluşturma
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect('/giris-yap/?next=' + request.path)

        title = request.POST.get("title")
        content = request.POST.get("content")
        category_ids = request.POST.getlist("categories")
        product_ids = request.POST.getlist("selected_products")

        if title and content and category_ids:
            thread = Thread.objects.create(
                title=title,
                content=content,
                user=request.user,
            )
            thread.categories.set(category_ids)

            # Seçilen ürünleri ekle
            if product_ids:
                thread.products.set(Product.objects.filter(id__in=product_ids))

            # Puan ver
            add_points(request.user, 'thread_create', 10)

            # İlgili başlıkları ata
            related = find_related_threads(thread)
            thread.related_threads.set(related)
            for r in related:
                r.related_threads.add(thread)

            # Session'daki seçili ürünleri temizle
            request.session['selected_product_ids'] = []

            messages.success(request, "Başlık başarıyla oluşturuldu!")
            return redirect("forum_page")

    return render(request, "forum.html", {
        "categories": categories,
        "threads": threads,
        "query": query,
        "products": products,
        "selected_products": selected_products,
        "product_ids": '&'.join([f"product_id={pid}" for pid in preselected_ids]),
        "selected_categories": list(map(int, category_filter)) if category_filter else [],
        "sort_by": sort_by,
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
     # Ürünlerle ana resimleri eşle
    product_images = {}
    for product in thread.products.all():
        main_image = product.images.filter(is_main=True).first()
        product_images[product.id] = main_image

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
    items = cart.items.select_related('product').all()
    total = sum(item.get_total_price() for item in items)
    return render(request, 'cart_detail.html', {
        'cart': cart,
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
def remove_from_favorites(request, product_id):
    Favorite.objects.filter(user=request.user, product_id=product_id).delete()
    messages.success(request, "Favorilerden çıkarıldı.")
    return redirect(request.META.get('HTTP_REFERER', 'favorite_list'))

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

def help(request):
    return render(request, 'help.html')


@login_required
def user_profile(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)

    # Profil güncelleme formu gönderildiyse
    if request.method == 'POST':
         # Şifre değişikliği formu doluysa
        if 'old_password' in request.POST and 'new_password1' in request.POST:
            password_form = PasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Kullanıcının oturumu açık kalsın
                messages.success(request, "Şifre başarıyla değiştirildi.")
                return redirect('user_profile')
            else:
                messages.error(request, "Şifre değiştirme başarısız. Lütfen bilgileri kontrol edin. Olası hatalar: Eski şifre yanlış, yeni şifreler eşleşmiyor, yeni şifre yeterince güçlü değil vb.")
                
        else:
            # User modeli bilgileri
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.email = request.POST.get('email', '')
            user.username = request.POST.get('email', '')
            user.save()

            # UserProfile bilgileri
            profile.nickname = request.POST.get('nickname', '')
            profile.phone = request.POST.get('phone', '')
            profile.address = request.POST.get('address', '')
            profile.avatar = request.POST.get('avatar', '')
            profile.save()

            messages.success(request, "Profiliniz başarıyla güncellendi.")

            return redirect('user_profile')  # Formdan sonra sayfayı yenile

    password_form = PasswordChangeForm(user=request.user)

    # Siparişler (tamamlananlar)
    completed_orders = Order.objects.filter(user=user, status='completed').order_by('-created_at')

   # Sepettekiler yerine beklemede olan sipariş ürünleri
    pending_orders = Order.objects.filter(user=user, status='pending').order_by('-created_at')

    now = datetime.now(timezone.utc)
    pending_order_items = []

    for order in pending_orders:
        items = order.items.select_related('product')
        for item in items:
            delta = now - order.created_at
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            duration_str = f"{days} gün {hours} saat {minutes} dakika"
            
            # item + bekleme süresini birlikte dict olarak ekle
            pending_order_items.append({
                'item': item,
                'duration': duration_str
            })

    # Ürün yorumları
    reviews = ProductReview.objects.filter(user=user).select_related('product')

    # Forum başlıkları
    threads = Thread.objects.filter(user=user).order_by('-created_at')

    context = {
        'user': user,
        'completed_orders': completed_orders,
        'pending_order_items': pending_order_items,
        'reviews': reviews,
        'threads': threads,
        'profile': profile,  # template içinde formda kullanmak için gerekli
        'password_form': password_form,
    }
    rewards = UserCouponReward.objects.filter(user=request.user).select_related('coupon')
    available_coupons = Coupon.objects.all()
    user_points, _ = UserPoint.objects.get_or_create(user=request.user)
    already_has_ids = list(rewards.values_list('coupon_id', flat=True))

    context.update({
        'rewards': rewards,
        'available_coupons': available_coupons,
        'user_points': user_points,
        'already_has_ids': already_has_ids,
    })


    return render(request, 'user_profile.html', context)

@login_required
def complete_order(request):
    cart = Cart.objects.get(user=request.user)
    cart_items = cart.items.all()

    if request.method == 'POST':
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        note = request.POST.get('note', '')

        if not address or not phone:
            messages.error(request, "Adres ve telefon bilgileri zorunludur.")
            return redirect('cart_detail')

        if not cart_items.exists():
            messages.warning(request, "Sepetinizde ürün yok.")
            return redirect('cart_detail')

        order = Order.objects.create(
            user=request.user,
            address=address,
            phone=phone,
            note=note,
            status='pending'
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price_at_order_time=item.product.price
            )

        cart_items.delete()
        messages.success(request, "Siparişiniz alındı. Onay sürecine geçildi.")
        return redirect('shopping')

    return redirect('cart_detail')

def urun_ara(request):# ürün adını arayarak listeliyor ve seçtiriyo ona gröe ekleniyor
    q = request.GET.get('q', '')
    urunler = Product.objects.filter(name__icontains=q)[:10]
    data = []
    for u in urunler:
        main_image = u.images.filter(is_main=True).first()
        data.append({
            "id": u.id,
            "name": u.name,
            "price": str(u.price),
            "image": main_image.image.url if main_image else "",  # Boş kalabilir
        })
    return JsonResponse(data, safe=False)

def clear_selected_products(request):# birden fazzla ürün eklenince seçimleri kaldırmaya yarayan kısım
    request.session['selected_product_ids'] = []
    return JsonResponse({'status': 'ok'})

def add_product_to_session(request, product_id):
    # Eğer kullanıcı giriş yapmamışsa giriş sayfasına yönlendir
    if not request.user.is_authenticated:
        messages.warning(request, "Ürün seçebilmek için giriş yapmalısınız.")
        return redirect('/login/?next=' + request.get_full_path())

    selected = request.session.get("selected_product_ids", [])
    if str(product_id) not in selected:
        selected.append(str(product_id))
        request.session["selected_product_ids"] = selected
        request.session.modified = True

    next_url = request.GET.get("next", "/forum/")
    return redirect(next_url)


MAX_REPORTS = 3  # Eşik sayısı
REPORT_PENALTY_THRESHOLD = 3  # Kaç farklı kullanıcıdan şikayet gelirse puan düşsün
REPORT_PENALTY_POINTS = 5    # Ceza olarak kaç puan düşülsün
def report_thread(request, thread_id):
    if not request.user.is_authenticated:
        return redirect('/giris-yap/?next=' + request.path)

    thread = get_object_or_404(Thread, id=thread_id)

    if request.method == 'POST':
        reason = request.POST.get('reason')

        # Aynı kullanıcı zaten şikayet ettiyse tekrar oluşturma
        already_reported = Report.objects.filter(
            reporter=request.user,
            report_type='thread',
            thread=thread
        ).exists()

        if not already_reported:
            Report.objects.create(
                reporter=request.user,
                report_type='thread',
                thread=thread,
                reason=reason
            )

            # ✅ Şikayet yeni bir kullanıcıdan geldiyse ceza uygula
            try:
                penalize_user(thread.user, REPORT_PENALTY_POINTS)
                PointHistory.objects.create(
                    user=thread.user,
                    action='report_penalty',
                    points=REPORT_PENALTY_POINTS,
                    content_type='thread',
                    object_id=thread.id
                )
                print("Yeni şikayet → Ceza uygulandı")
            except Exception as e:
                print("Ceza puanı verirken hata:", e)

        # Gizleme sınırını geçtiyse başlığı gizle
        report_count = Report.objects.filter(
            thread=thread,
            report_type='thread',
            status='pending'
        ).values('reporter').distinct().count()

        if report_count >= MAX_REPORTS and not thread.is_hidden:
            thread.is_hidden = True
            thread.save(update_fields=['is_hidden'])
            print("Başlık gizlendi")

        return redirect("thread_detail", thread_id=thread.id)

    return render(request, 'report_form.html', {'object': thread, 'type': 'thread'})


def report_reply(request, reply_id):
    if not request.user.is_authenticated:
        return redirect('/giris-yap/?next=' + request.path)

    reply = get_object_or_404(Reply, id=reply_id)

    if request.method == 'POST':
        reason = request.POST.get('reason')
        Report.objects.create(
            reporter=request.user,
            report_type='reply',
            reply=reply,
            reason=reason
        )
        return redirect("thread_detail", thread_id=reply.thread.id)

    return render(request, 'report_form.html', {'object': reply, 'type': 'reply'})

# forum/views.py içindeki forum_page fonksiyonu içinde başlık oluşturduktan sonra:

# Puan sistemi
from .models import UserPoint, PointHistory



from django.shortcuts import redirect, get_object_or_404
from django.http import HttpResponseForbidden

from .models import Reply, UserPoint, PointHistory  # model yolunu kendi projen göre ayarla

def mark_best_reply(request, reply_id):
    if not request.user.is_authenticated:
        return redirect(f'/giris-yap/?next={request.path}')

    reply = get_object_or_404(Reply, id=reply_id)
    thread = reply.thread

    if request.user != thread.user:
        return HttpResponseForbidden("Bu işlem sadece başlığı açan kişi tarafından yapılabilir.")

    # Önceki en iyi cevap varsa kaldır ve puanı geri al
    old_best = Reply.objects.filter(thread=thread, is_best=True).first()

    if old_best:
        if old_best.id == reply.id:
            # Toggle: aynı cevap yeniden seçildiyse kaldır
            old_best.is_best = False
            old_best.save()
            add_points(old_best.user, 'reply_best', -10, related_reply=old_best)
            return redirect('thread_detail', thread_id=thread.id)

        # Farklı cevabı en iyi yaparken öncekini kaldır
        old_best.is_best = False
        old_best.save()
        add_points(old_best.user, 'reply_best', -10, related_reply=old_best)

    # Yeni cevabı en iyi olarak ata
    reply.is_best = True
    reply.save()
    add_points(reply.user, 'reply_best', 10, related_reply=reply)

    return redirect('thread_detail', thread_id=thread.id)

# views.py
from django.contrib.auth.decorators import login_required
from .models import UserCouponReward

@login_required
def my_coupons(request):
    user = request.user
    rewards = UserCouponReward.objects.filter(user=user).select_related('coupon', 'rank')
    user_points, _ = UserPoint.objects.get_or_create(user=user)  # 👈 bu satır düzeltildi
    available_coupons = Coupon.objects.all()
    already_has_ids = list(rewards.values_list('coupon_id', flat=True))

    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_id')
        try:
            coupon = Coupon.objects.get(id=coupon_id)
        except Coupon.DoesNotExist:
            return render(request, 'my_coupons.html', {'error': 'Kupon bulunamadı.'})

        # Yetersiz puan kontrolü
        if user_points.total_points < coupon.required_points:
            return render(request, 'my_coupons.html', {
                'error': 'Yetersiz puan.',
                'user_points': user_points,
                'rewards': rewards,
                'available_coupons': available_coupons
            })

        # Zaten alınmış mı?
        if UserCouponReward.objects.filter(user=request.user, coupon=coupon).exists():
            return render(request, 'my_coupons.html', {
                'error': 'Bu kuponu zaten aldınız.',
                'user_points': user_points,
                'rewards': rewards,
                'available_coupons': available_coupons
            })

        # Ödülü oluştur
        UserCouponReward.objects.create(
            user=request.user,
            coupon=coupon
        )

        # Puan düş
        user_points.total_points -= coupon.required_points
        user_points.save()

        return redirect('my_coupons')

    return render(request, 'my_coupons.html', {
        'user_points': user_points,
        'rewards': rewards,
        'available_coupons': available_coupons
    })


def add_points(user, action, points, related_reply=None):
    user_points, _ = UserPoint.objects.get_or_create(user=user)
    user_points.total_points += points
    user_points.rank_points += points
    user_points.save()
    user_points.update_rank()

    PointHistory.objects.create(
        user=user,
        action=action,
        points=points,
        related_reply=related_reply  # varsa kaydedilir
    )

def penalize_user(user, penalty_points):
    user_points, _ = UserPoint.objects.get_or_create(user=user)

    user_points.total_points -= penalty_points      # kupon için de düşüyorsa buna dokun
    user_points.rank_points -= penalty_points        # rütbeyi etkileyen kısım, önemli
    user_points.save()
    user_points.update_rank()

    PointHistory.objects.create(
        user=user,
        action='report_penalty',
        points=-penalty_points
    )

def redeem_coupon(user, coupon, cost):
    user_points = UserPoint.objects.get(user=user)
    if user_points.total_points >= cost:
        user_points.total_points -= cost
        user_points.save()
        PointHistory.objects.create(user=user, action='coupon_redeem', points=-cost)
        UserCouponReward.objects.create(user=user, coupon=coupon)
        return True
    return False
