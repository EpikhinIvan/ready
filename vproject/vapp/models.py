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
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    sector = models.CharField(max_length=100)
    row = models.IntegerField()
    seat = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    def update_total_price(self):
        order_items = self.orderitem_set.all()
        self.total_price = sum(item.price * item.quantity for item in order_items)
        self.save()

@receiver(post_save, sender=Order)
def update_order_total_price(sender, instance, created, **kwargs):
    if created:
        instance.update_total_price()

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
