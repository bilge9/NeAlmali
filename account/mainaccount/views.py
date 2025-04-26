from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def register(request):
    return render(request, 'register.html')

def login_view(request):  # 'login' ismi Python'da gömülü olduğu için '_view' ekledik
    return render(request, 'login.html')

def shopping(request):
    return render(request, 'shopping.html')

def shop_categories(request):
    return render(request, 'shop_categories.html')
# Create your views here.
