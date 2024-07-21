from django import forms
from .models import Product


class MessageForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea, label='Message')



class BotStatusForm(forms.Form):
    is_active = forms.BooleanField(required=False, label="Бот активен")
    


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'quantity', 'price', 'category']