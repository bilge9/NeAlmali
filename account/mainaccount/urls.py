from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path( 'shopping/', views.shopping, name='shopping'),
    path('shop/category/<int:category_id>/', views.shop_categories, name='shop_categories'),
    path('forum/', views.forum, name='forum'),
    path('forum_caption/', views.forum_caption, name='forum_caption'),
    path('product_info/', views.product_info, name='product_info'),

]
