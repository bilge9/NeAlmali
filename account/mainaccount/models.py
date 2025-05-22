from django.db import models
from django.contrib.auth.models import User 
from mptt.models import MPTTModel, TreeForeignKey
from django.db.models import Avg
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class SellerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    store_name = models.CharField(max_length=100)
    bio = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)  # Admin onayı

    def __str__(self):
        return f"{self.user.username} - {self.store_name}"
    
    @property
    def average_rating(self):
        # Bu satıcının ürünleri
        seller_products = Product.objects.filter(seller=self.user)
        # Bu ürünlere ait tüm yorumlardan seller_rating değerleri
        seller_reviews = ProductReview.objects.filter(product__in=seller_products, seller_rating__isnull=False)
        # Ortalamayı al
        avg = seller_reviews.aggregate(Avg('seller_rating'))['seller_rating__avg']
        return round(avg, 1) if avg else None
    
class UserProfile(models.Model):
    AVATAR_CHOICES = [
        ('avatar1.jpeg', 'Avatar 1'),
        ('avatar2.jpeg', 'Avatar 2'),
        ('avatar3.jpeg', 'Avatar 3'),
        ('avatar4.jpeg', 'Avatar 4'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    avatar = models.CharField(max_length=100, choices=AVATAR_CHOICES, blank=True)

    def __str__(self):
        return f"{self.user.username} Profili"

    def avatar_url(self):
        if self.avatar:
            return f"/static/avatars/{self.avatar}"
        return "/static/avatars/default.png"

class Category(MPTTModel):
    name = models.CharField(max_length=100)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    image = models.ImageField(upload_to='category_images/', null=True, blank=True, verbose_name="Ana Resim")
    hover_image = models.ImageField(upload_to='category_images/', null=True, blank=True, verbose_name="Hover Resim")
    highlighted = models.BooleanField(default=False, verbose_name="Öne Çıkan Kategori")

    def __str__(self):
        return self.name

    class MPTTMeta:
        order_insertion_by = ['name']

class Product(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    @property #propertyle resmi atamayı yt ekledi
    def main_image(self):
        return self.images.filter(is_main=True).first()
    @property
    def average_rating(self):
        avg = self.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else None

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')
    is_main = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} - Image" if self.is_main else f"{self.product.name} - Additional Image"

class Attribute(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class CategoryAttribute(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.category.name} - {self.attribute.name}"
    
class ProductAttributeValue(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attribute_values')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.product.name} - {self.attribute.name}: {self.value}"

class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    # Yeni alanlar:
    image = models.ImageField(upload_to='review_images/', null=True, blank=True)
    seller_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'product'], name='unique_product_review')
        ]

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

#forum veritabanı modelleri
class ForumCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
        
class Thread(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='threads')
    created_at = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(ForumCategory, related_name='threads')
    views = models.PositiveIntegerField(default=0)
    like_count = models.IntegerField(default=0)
    dislike_count = models.IntegerField(default=0)
    related_threads = models.ManyToManyField('self', blank=True)
    is_hidden = models.BooleanField(default=False)
    products = models.ManyToManyField(Product, blank=True)

    def __str__(self):
        return self.title

    def update_vote_counts(self):
        self.like_count = self.votes.filter(value='like').count()
        self.dislike_count = self.votes.filter(value='dislike').count()
        self.save(update_fields=['like_count', 'dislike_count'])


class ThreadVote(models.Model):
    LIKE_CHOICES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='votes')  # related_name ekledik
    value = models.CharField(choices=LIKE_CHOICES, max_length=7)
    
    class Meta:
        unique_together = ('user', 'thread')  # Aynı kullanıcı aynı başlığa bir kere oy verebilsin


# mainaccount/models.py

class Reply(models.Model):
    thread = models.ForeignKey(Thread, related_name="replies", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=2)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_hidden = models.BooleanField(default=False)
    is_best = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Reply by {self.user.username} on {self.thread.title}"



#Sepet veritabanı

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'nin Sepeti"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.product.name} - {self.quantity} adet"

    def get_total_price(self):
        return self.quantity * self.product.price
    
#favorilerim

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # Aynı ürün bir kez favorilere eklenebilsin

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"
    
# Alışveriş geçmişi
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('completed', 'Tamamlandı'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    address = models.CharField(max_length=255, default='Adres girilmedi')
    phone = models.CharField(max_length=20, default='Telefon girilmedi')
    note = models.TextField(blank=True, default='')
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)


    # 🔽 Kupon sistemi eklemeleri:
    coupon = models.ForeignKey('Coupon', null=True, blank=True, on_delete=models.SET_NULL)
    coupon_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()} - {self.created_at.strftime('%Y-%m-%d')}"

    def get_total_price(self):
        total = sum(item.get_total_price() for item in self.items.all())
        if self.coupon_used and self.coupon:
            total -= self.coupon.discount_amount
            if total < 0:
                total = 0
        return total


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price_at_order_time = models.DecimalField(max_digits=10, decimal_places=2)

    def get_total_price(self):
        return self.quantity * self.price_at_order_time

class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('thread', 'Başlık'),
        ('reply', 'Yorum'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Beklemede'),
        ('accepted', 'Kabul Edildi'),
        ('rejected', 'Reddedildi'),
    ]

    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES)
    thread = models.ForeignKey('Thread', on_delete=models.CASCADE, null=True, blank=True)
    reply = models.ForeignKey('Reply', on_delete=models.CASCADE, null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    resolution_detail = models.TextField(blank=True, null=True, help_text="Kararın gerekçesi (isteğe bağlı).")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.report_type} raporu ({self.status})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Otomatik gizleme/gösterme
        if self.status == 'accepted':
            if self.report_type == 'thread' and self.thread:
                self.thread.is_hidden = True
                self.thread.save(update_fields=['is_hidden'])
            elif self.report_type == 'reply' and self.reply:
                self.reply.is_hidden = True
                self.reply.save(update_fields=['is_hidden'])

        elif self.status == 'rejected':
            # Tüm raporlar kontrol edilir — accepted yoksa is_hidden False yapılır
            if self.report_type == 'thread' and self.thread:
                if not Report.objects.filter(thread=self.thread, status='accepted').exists():
                    self.thread.is_hidden = False
                    self.thread.save(update_fields=['is_hidden'])
            elif self.report_type == 'reply' and self.reply:
                if not Report.objects.filter(reply=self.reply, status='accepted').exists():
                    self.reply.is_hidden = False
                    self.reply.save(update_fields=['is_hidden'])


class Rank(models.Model):
    name = models.CharField(max_length=50)
    min_points = models.IntegerField()
    

    def __str__(self):
        return f"{self.name} ({self.min_points} puan)"

class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    discount_amount = models.IntegerField(default=0)
    required_points = models.IntegerField(default=100)  # EKLENDİ
    created_at = models.DateTimeField(auto_now_add=True)
    required_rank = models.ForeignKey(Rank, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.code} - {self.discount_amount} TL"

class UserCouponReward(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rank = models.ForeignKey('Rank', on_delete=models.CASCADE, null=True, blank=True )
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    rewarded_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    class Meta:
        unique_together = ('user', 'coupon')  # Her kullanıcıya aynı rütbeden bir kez verilir

    def __str__(self):
        return f"{self.user.username} - {self.rank.name} kuponu"


class UserPoint(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="points")
    total_points = models.IntegerField(default=0)
    rank_points = models.IntegerField(default=0)   # Sadece rütbe için kullanılır (kupon harcarken düşmez, şikayetle düşer)
    rank = models.ForeignKey(Rank, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.total_points} puan - {self.rank.name if self.rank else 'Rütbesiz'}"

    def update_rank(self):
        new_rank = Rank.objects.filter(min_points__lte=self.rank_points).order_by('-min_points').first()
        if new_rank and new_rank != self.rank:
            self.rank = new_rank
            self.save()

        #Hediye kupon verme (rütbe ile)
            special_coupons = Coupon.objects.filter(required_rank=new_rank)  # böyle bir alan varsa
            for coupon in special_coupons:
                if not UserCouponReward.objects.filter(user=self.user, coupon=coupon).exists():
                    UserCouponReward.objects.create(
                        user=self.user,
                        coupon=coupon,
                        rank=new_rank  # burası önemli
                    )



class PointHistory(models.Model):
    ACTION_CHOICES = [
        ('thread_create', 'Başlık Açma'),
        ('reply_best', 'En İyi Cevap'),
        ('coupon_redeem', 'Kupon Kullanımı'),
        # gerekirse daha fazlası eklenir
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="point_histories")
    action = models.CharField(choices=ACTION_CHOICES, max_length=20)
    points = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    related_reply = models.ForeignKey('Reply', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.points} puan"

