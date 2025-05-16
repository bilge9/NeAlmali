from django import forms
from .models import ProductReview ,Product

class ProductReviewForm(forms.ModelForm):
    class Meta:
        model = ProductReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.HiddenInput(),  # Gizli input
            'comment': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'brand', 'category','description', 'price' ]