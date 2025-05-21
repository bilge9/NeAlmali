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
    SellerProfile,
    UserProfile,
    Order,
    OrderItem,
    Report,
    Rank,
    Coupon,
    
)
from django.contrib.auth.models import User
from mptt.admin import DraggableMPTTAdmin

# === ProductAttributeValue Inline ===
class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1

# === ProductImage Inline ===
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

# === SellerProfile Admin ===
@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'store_name', 'is_approved']
    list_filter = ['is_approved']

# === Product Admin ===
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'seller')  
    search_fields = ('name', 'category__name', 'seller__username')  
    list_filter = ('category',)
    ordering = ('-price',)
    inlines = [ProductAttributeValueInline, ProductImageInline]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "seller":
            kwargs["queryset"] = User.objects.filter(seller_profile__isnull=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
    filter_horizontal = ('categories',)  # Categories alanını yan yana görsel olarak seçilebilir kılar

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

# === Order Admin ===
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

# === Order Admin ===
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    actions = ['mark_as_completed']

    @admin.action(description='Seçilen siparişleri tamamlandı olarak işaretle')
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f"{updated} sipariş başarıyla tamamlandı.")

# === OrderItem Admin ===
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price_at_order_time', 'get_total_price')
    search_fields = ('order__user__username', 'product__name')
    list_filter = ('order__status',)
    ordering = ('-order__created_at',)

# === UserProfile Admin ===
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'nickname', 'phone', 'address', 'avatar')
    search_fields = ('user__username', 'nickname')
    list_filter = ('avatar',)
    ordering = ('user__username',)

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'thread', 'report_type', 'status', 'reporter', 'reason', 'created_at', 'is_thread_hidden')
    list_filter = ('report_type', 'status', 'created_at')
    search_fields = ('reason',)
    actions = ['mark_reviewed', 'mark_resolved', 'mark_rejected']

    def is_thread_hidden(self, obj):
        if obj.report_type == 'thread' and obj.thread:
            return obj.thread.is_hidden
        return '-'
    is_thread_hidden.boolean = True
    is_thread_hidden.short_description = 'Başlık Gizli mi?'

    def mark_resolved(self, request, queryset):
        for report in queryset:
            report.status = 'accepted'
            report.save()
    mark_resolved.short_description = "Seçilenleri 'Kabul Edildi' olarak işaretle"

    def mark_rejected(self, request, queryset):
        for report in queryset:
            report.status = 'rejected'
            report.save()
    mark_rejected.short_description = "Seçilenleri 'Reddedildi' olarak işaretle"


@admin.register(Rank)
class RankAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_points')
    ordering = ('min_points',)
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'description', 'discount_amount', 'required_points', 'created_at')
    search_fields = ('code', 'description')
    list_filter = ('required_points', 'created_at')
    ordering = ('required_points',)
