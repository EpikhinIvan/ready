# from django import forms
# from django.forms import modelformset_factory
# from .models import Product

# class ProductForm(forms.ModelForm):
#     class Meta:
#         model = Product
#         fields = ['name', 'description', 'price', 'category', 'available_quantity']

# # Создание формсета для продуктов
# ProductFormSet = modelformset_factory(Product, form=ProductForm, extra=0)
from django import forms

class MessageForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, label='Сообщение')
class BotStatusForm(forms.Form):
    is_active = forms.BooleanField(required=False, label="Бот активен")