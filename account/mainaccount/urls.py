from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path( 'shopping/', views.shopping, name='shopping'),
    path('shop/category/<int:category_id>/', views.shop_categories, name='shop_categories'),
    path('shop/category/product_info/<int:product_id>/', views.product_info, name='product_info'),
    
    path('forum/', views.forum_page, name='forum_page'),
    path('forum-autocomplete/', views.forum_autocomplete, name='forum_autocomplete'),
    path('thread/<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('baslik/<int:thread_id>/yanitla/', views.reply_create, name='reply_create'),
    path('thread/<int:thread_id>/vote/<str:vote_type>/', views.vote_thread, name='vote_thread'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('category/<int:category_id>/threads/', views.category_threads, name='category_threads'),
    path('kategoriler/', views.category_list, name='category_list'),
    #sepet
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    #favorilerim
    path('favorites/add/<int:product_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('favorites/', views.favorite_list, name='favorite_list'),
    path('seller/profile/', views.seller_profile, name='seller_profile'),
]
