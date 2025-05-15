from django.contrib import admin
from .models import (
    Product,
    Category,
    ProductImage,
    Attribute,
    CategoryAttribute,
    ProductAttributeValue,
    Thread,
    ForumCategory,
    Reply,
    Cart,
    CartItem,
    Favorite,
    ProductReview,
)
from mptt.admin import MPTTModelAdmin, DraggableMPTTAdmin
# === ProductAttributeValue Inline ===
class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1

# === ProductImage Inline ===
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

# === Product Admin ===
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category')
    search_fields = ('name', 'category__name')
    list_filter = ('category',)
    ordering = ('-price',)
    inlines = [ProductAttributeValueInline, ProductImageInline]

# === Category Admin (MPTT ile) ===
@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ('tree_actions', 'indented_title', 'highlighted')
    list_filter = ('highlighted',)
    search_fields = ('name',)

# === ProductImage Admin ===
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'is_main')
    list_filter = ('is_main',)

# === Attribute Admin ===
@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name',)

# === CategoryAttribute Admin ===
@admin.register(CategoryAttribute)
class CategoryAttributeAdmin(admin.ModelAdmin):
    list_display = ('category', 'attribute')

# === ProductAttributeValue Admin ===
@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'attribute', 'value')
    list_filter = ('attribute',)

# === Thread Admin ===
@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'like_count', 'dislike_count')
    filter_horizontal = ('categories',)

# === ForumCategory Admin ===
@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

# === Reply Admin ===
@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('user', 'thread', 'content', 'created_at')
    search_fields = ('user__username', 'content')
    list_filter = ('created_at',)

#Sepet veritabanı

admin.site.register(Cart)
admin.site.register(CartItem)

#favoriler

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__username', 'product__name')
    list_filter = ('created_at',)

# === ProductReview Admin ===
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    search_fields = ('product__name', 'user__username')
    list_filter = ('rating', 'created_at')
    ordering = ('-created_at',)