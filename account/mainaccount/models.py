from django.db import models
from django.contrib.auth.models import User#yt
from mptt.models import MPTTModel, TreeForeignKey

# Create your models here.

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
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    brand = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

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



class Reply(models.Model):
    thread = models.ForeignKey(Thread, related_name="replies", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=2)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
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