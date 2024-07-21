from django.contrib import admin
from .models import Product, Order


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'quantity', 'price', 'category']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['userid', 'items', 'total_price', 'sector_row_seat', 'created_at', 'status', 'order_number']

    def sector_row_seat(self, obj):
        return f"{obj.sector} | {obj.row}-Ряд | {obj.seat}-Место"
    sector_row_seat.short_description = 'Сектор, Ряд, Место'

