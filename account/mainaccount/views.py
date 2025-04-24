from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def register(request):
    return render(request, 'register.html')

def login_view(request):  # 'login' ismi Python'da gömülü olduğu için '_view' ekledik
    return render(request, 'login.html')
# Create your views here.
