from django.contrib import admin
from django.contrib import admin
from .models import Product, Order, OrderItem, Courier

admin.site.register(Product)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Courier)

