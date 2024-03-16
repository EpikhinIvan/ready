from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login
from .models import Product
from .models import Order
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import csv
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from .models import Helper
from .models import Order

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
            error_message = 'Invalid username or password. Please try again.'

    return render(request, 'login.html', {'error_message': error_message})

@login_required(login_url='log_in')
def get_orders_data(request):
    orders = Order.objects.all()
    data = []
    for order in orders:
        data.append({
            'id': order.id,
            'created_at': order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'status': order.get_status_display(),
            'products': ', '.join([item.product.name for item in order.orderitem_set.all()]),
            'cost': sum([item.price for item in order.orderitem_set.all()]),
            'courier': order.courier.user.username,
        })

    return JsonResponse({'data': data})



def orders_view(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'orders.html', {'order-list': orders})


@csrf_exempt
@login_required(login_url='log_in')
def export_orders_csv(request):
    orders = Order.objects.all()
    data = []

    for order in orders:
        data.append({
            'id': order.id,
            'created_at': order.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'status': order.get_status_display(),
            'products': ', '.join([item.product.name for item in order.orderitem_set.all()]),
            'cost': sum([item.price for item in order.orderitem_set.all()]),
            'courier': order.courier.user.username,
        })

    # Генерируем CSV и возвращаем его как файл
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'

    writer = csv.writer(response)
    # Заголовки CSV
    writer.writerow(['ID', 'Date', 'Status', 'Product', 'Cost', 'Courier'])

    # Записываем данные в CSV
    for order in data:
        writer.writerow([order['id'], order['created_at'], order['status'], order['products'], order['cost'], order['courier']])

    return response


 


@login_required(login_url='log_in')
def product_list(request):
    products = Product.objects.all()
    return render(request, 'product_list.html', {'products': products})
    

@login_required(login_url='log_in')
def get_products_data(request):
    products = Product.objects.all()
    data = []
    for product in products:
        data.append({
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
def order_details(request):
    pass

@login_required(login_url='log_in')
def analytics(request):
    pass



@login_required(login_url='log_in')
def product_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')
        category = request.POST.get('category')

        Product.objects.create(name=name, price=price, quantity=quantity, category=category)

        return redirect('product_list')  

    return render(request, 'product_create.html')



# вся страница настроек
@login_required(login_url='log_in')
def settings(request):
    return render(request, 'settings.html')



@login_required(login_url='log_in')
def set_helper(request):
    if request.method == 'POST':
        telegram_username = request.POST.get('telegram_username')

        helper, created = Helper.objects.get_or_create(telegram_username=telegram_username)

        if not created:
            helper.telegram_username = telegram_username
            helper.save()

    return HttpResponse("Helper set successfully!")


@login_required(login_url='log_in')
def stop_bot(request):
    # Обработка остановки бота
    if request.method == 'POST':
        pass

    return HttpResponse("Bot stopped successfully!")

@login_required(login_url='log_in')
def set_match_time(request):
    # Обработка установки времени работы матча
    if request.method == 'POST':
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        # Ваш код обработки

    return HttpResponse("Match time set successfully!")