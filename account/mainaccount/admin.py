from django.contrib import admin
from .models import (
    Category,
    Product,
    ProductImage,
    Attribute,
    CategoryAttribute,
    ProductAttributeValue
)
from mptt.admin import MPTTModelAdmin

# Register your models here.

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
    list_display = ('name', 'category', 'price', 'created_at')
    list_filter = ('category',)
    search_fields = ('name',)
    inlines = [ProductAttributeValueInline, ProductImageInline]

# === Category Admin ===
@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'parent')
    search_fields = ('name',)

# === ProductImage Admin (tek başına da görüntülenebilsin) ===
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

# === ProductAttributeValue Admin (isteğe bağlı olarak) ===
@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('product', 'attribute', 'value')
    list_filter = ('attribute',)
