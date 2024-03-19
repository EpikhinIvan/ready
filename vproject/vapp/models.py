from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Product(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    

class Helper(models.Model):
    telegram_username = models.CharField(max_length=255)

    def __str__(self):
        return self.telegram_username

class Courier(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

class Order(models.Model):
    items = models.TextField()  # Простое текстовое поле для хранения списка товаров
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sector = models.CharField(max_length=100)
    row = models.IntegerField()
    seat = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"
#ГЫГЫЫГ
class Chat(models.Model):
    chat_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255, null=True, blank=True)  # Тег пользователя
    first_name = models.CharField(max_length=255, null=True, blank=True)  # Имя пользователя

    def __str__(self):
        return f"@{self.username}" if self.username else str(self.chat_id)
##ДЛЯ ВЕЛЮЧЕНИЯ И ВЫКЛЮЧЕНИЯ    
class BotStatus(models.Model):
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "Активен" if self.is_active else "Не активен"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class BotStatus(models.Model):
    is_active = models.BooleanField(default=True)
    scheduled_time = models.DateTimeField()

class BotMessage(models.Model):
    user_telegram_id = models.PositiveIntegerField()
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class SiteStatistics(models.Model):
    total_users = models.PositiveIntegerField()
    today_users = models.PositiveIntegerField()
    total_orders = models.PositiveIntegerField()
    total_order_amount = models.DecimalField(max_digits=10, decimal_places=2)

class TimeSlot(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()



class BotUser(models.Model):
    user_id = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    username = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"@{self.username}" if self.username else self.first_name