from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from .models import Product, BotStatus, Order, Chat, BotUser, Helper
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import csv
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .forms import MessageForm, BotStatusForm, ProductForm
import telebot
from django.views.decorators.csrf import csrf_exempt




TOKEN = '6014766028:AAGQtwWJuFpOFvDeEYGKlzzPgc2gZAMJkfc'
bot = telebot.TeleBot(TOKEN)

@login_required(login_url='log_in')
def send_message_to_all(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            chats = Chat.objects.all()
            for chat in chats:
                try:
                    bot.send_message(chat.chat_id, message)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения: {e}")
            return redirect('settings')
    else:
        form = MessageForm()

    return render(request, 'message.html', {'form': form})



@login_required(login_url='log_in')
def change_bot_status(request):
    if request.method == "POST":
        form = BotStatusForm(request.POST)
        if form.is_valid():
            is_active = form.cleaned_data['is_active']
            BotStatus.objects.update_or_create(id=1, defaults={'is_active': is_active})
            return redirect('settings')  
    else:
        status, _ = BotStatus.objects.get_or_create(id=1)
        form = BotStatusForm(initial={'is_active': status.is_active})

    return render(request, 'settings.html', {'form': form})




def log_in(request):
    error_message = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('order-list')  
        else:
            error_message = 'Такого пользователя не существует'

    return render(request, 'login.html', {'error_message': error_message})




@login_required(login_url='log_in')
def get_orders_data(request):
    orders = Order.objects.all()
    data = []
    for order in orders:
        data.append({
            'userid' : order.userid,
            'items' : order.items,
            'created_at': order.created_at.strftime("%m-%d %H:%M"),
            'sector': order.sector,
            'row' : order.row,
            'seat' : order.seat,
            'total_price': order.total_price,
            'order_number': order.order_number,
            'status': order.status
        })

    return JsonResponse({'data': data})


@csrf_exempt
def confirm_payment(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        
        try:
            order = Order.objects.get(pk=order_id)  # Получаем заказ по его ID
            user_id = order.userid  # Получаем ID пользователя из заказа
            message = f"Оплата за заказ №{order.order_number} подтверждена."
            
            # Поскольку user_id это не chat_id, вам нужно будет получить chat_id из модели Chat
            # Например, предполагаем, что userid это username пользователя в Telegram
            try:
                chat = Chat.objects.get(username=user_id)  # Получаем объект чата по username
                bot.send_message(chat_id=chat.chat_id, text=message)
                return JsonResponse({'success': True})
            except Chat.DoesNotExist:
                return JsonResponse({'error': 'User chat not found'}, status=404)
                
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)



@csrf_exempt
@login_required(login_url='log_in')
def export_orders_csv(request):
    orders = Order.objects.all()
    data = []

    for order in orders:
        data.append({
            "id" : order.id,
            'userid' : order.userid,
            'items' : order.items,
            'created_at': order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'sector': order.sector,
            'row' : order.row,
            'seat' : order.seat,
            'total_price': order.total_price,
            'order_number': order.order_number,
        })

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'UserId', 'Items', 'Date', 'Sector', 'Row', 'Seat' , 'TotalPrice', 'OrderNumber'])

    for order in data:
        writer.writerow([order['id'], order['userid'], order['items'], order['created_at'], order['sector'], order['row'], order['seat'], order['total_price'], order['order_number']])

    return response




def user_list(request):
    users = Chat.objects.all()
    return render(request, 'user_list.html', {'users': users})





@login_required(login_url='log_in')
def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})





@login_required(login_url='log_in')
def edit_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')  
    else:
        form = ProductForm(instance=product)

    return render(request, 'product_edit.html', {'form': form, 'product': product})




@login_required(login_url='log_in')
def delete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        product.delete()
        return redirect('product_list') 
        
    return render(request, 'product_edit.html', {'product': product})




@login_required(login_url='log_in')
def get_products_data(request):
    products = Product.objects.all()
    data = []
    for product in products:
        data.append({
            'id': product.id,
            'category': product.category,
            'name': product.name,
            'quantity': product.quantity,
            'price': product.price,
        })

    return JsonResponse({'data': data})




@login_required(login_url='log_in')
def order_list(request):
    orders = Order.objects.all()
    return render(request, 'orders.html', {'orders': orders})





@login_required(login_url='log_in')
def order_details(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    
    return render(request, 'order_details.html', {'order': order})






@login_required(login_url='log_in')
def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        category = request.POST.get('category')

        # Создаем экземпляр продукта
        new_product = Product.objects.create(name=name, price=price, quantity=quantity, category=category)
        
        # Устанавливаем initial_quantity равным quantity
        new_product.initial_quantity = new_product.quantity
        new_product.save()

        return redirect('product_list')  
    return render(request, 'product_create.html')




@login_required(login_url='log_in')
def settings(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.cleaned_data['message']
            chats = Chat.objects.all()
            for chat in chats:
                try:
                    bot.send_message(chat.chat_id, message)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения: {e}")
            return redirect('settings')
    else:
        form = MessageForm()

    status, _ = BotStatus.objects.get_or_create(id=1)
    bot_status_form = BotStatusForm(initial={'is_active': status.is_active})

    return render(request, 'settings.html', {'form': form, 'bot_status_form': bot_status_form})



@login_required(login_url='log_in')
def set_helper(request):
    if request.method == 'POST':
        telegram_username = request.POST.get('telegram_username')

        helper, created = Helper.objects.get_or_create(telegram_username=telegram_username)

        if not created:
            helper.telegram_username = telegram_username
            helper.save()

    return redirect("settings")

