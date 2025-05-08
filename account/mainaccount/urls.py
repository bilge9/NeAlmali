from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path( 'shopping/', views.shopping, name='shopping'),
    path('shop/category/<int:category_id>/', views.shop_categories, name='shop_categories'),
    path('forum/', views.forum_page, name='forum_page'),
    path('thread/<int:thread_id>/', views.thread_detail, name='thread_detail'),
    path('product_info/', views.product_info, name='product_info'),
    path('baslik/<int:thread_id>/yanitla/', views.reply_create, name='reply_create'),
    path('thread/<int:thread_id>/vote/<str:vote_type>/', views.vote_thread, name='vote_thread'),
    path('category/<int:category_id>/', views.category_detail, name='category_detail'),
    path('category/<int:category_id>/threads/', views.category_threads, name='category_threads'),
    path('kategoriler/', views.category_list, name='category_list'),
]
