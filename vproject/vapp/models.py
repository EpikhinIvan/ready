from django.db import models
from django.contrib.auth.models import User
from django.db import models
import uuid
from django.utils import timezone

class Product(models.Model):
    name = models.CharField(max_length=255, verbose_name='Продукт')
    quantity = models.PositiveIntegerField(verbose_name='количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='цена')
    category = models.CharField(max_length=255, verbose_name='категория')

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Продукты"
    
def generate_order_number():
    return uuid.uuid4().hex[:6].upper()

class Order(models.Model):
    STATUS_CHOICES = [
        ('New', 'Новая'),
        ('Paid', 'Оплачено'),
        ('Closed', 'Закрыта'),
    ]
    userid = models.CharField(max_length=30, default='-', verbose_name='id')
    items = models.TextField(verbose_name='корзина')  
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='общая сумма')
    sector = models.CharField(max_length=100, verbose_name='сектор')
    row = models.CharField(max_length=10,verbose_name='ряд')
    seat = models.IntegerField(verbose_name='место')
    created_at = models.DateTimeField(default=timezone.now, verbose_name='создано')    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='New', verbose_name='статус')
    order_number = models.CharField(max_length=20, default='-', verbose_name='номер заказа')

    class Meta:
        verbose_name_plural = "Заказы"

    def mark_as_paid(self):
        if self.status != 'Paid':
            self.status = 'Paid'
            self.save(update_fields=['status'])


class Helper(models.Model):
    telegram_username = models.CharField(max_length=255)

    def __str__(self):
        return self.telegram_username



class Chat(models.Model):
    chat_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255, null=True, blank=True) 
    first_name = models.CharField(max_length=255, null=True, blank=True)  

    def __str__(self):
        return f"@{self.username}" if self.username else str(self.chat_id)
    


class BotStatus(models.Model):
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return "Активен" if self.is_active else "Не активен"
    


class BotMessage(models.Model):
    user_telegram_id = models.PositiveIntegerField()
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    


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