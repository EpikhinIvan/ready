from django.core.management.base import BaseCommand
from telebot import TeleBot, types
from django.db.models import F
from vapp.models import Product
from decimal import Decimal
from vapp.models import Order

bot = TeleBot('7171828502:AAHfKBNkG1zTgNtf79YCViNBCOKECvgGqTM')

user_data = {}

def ensure_user_data_initialized(user_id):
        user_data[user_id] = {
            'order': {
                'items': [],
                'total_price': Decimal('0.0'),
                'sector': None,
                'row': None,
                'seat': None
            }
        }
#START
@bot.message_handler(commands=['start'])
def start_order(message):
    user_id = message.chat.id
    ensure_user_data_initialized(user_id)
    show_categories(user_id)
#FOOD
def show_categories(user_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    button_food = types.InlineKeyboardButton("Еда", callback_data='select_food')
    button_drink = types.InlineKeyboardButton("Напитки", callback_data='select_drink')
    markup.add(button_food, button_drink)
    bot.send_message(user_id, "Что вы хотели бы добавить к заказу?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('select_'))
def select_product_category(call):
    user_id = call.from_user.id
    category = call.data.split('_')[1].upper()
    products = Product.objects.filter(category=category).values('id', 'name')
    markup = types.InlineKeyboardMarkup(row_width=1)
    for product in products:
        button = types.InlineKeyboardButton(product['name'], callback_data=f"product_{product['id']}")
        markup.add(button)
    bot.send_message(user_id, f"Выберите {category.lower()}:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
def add_product_to_order(call):
    user_id = call.from_user.id
    product_id = int(call.data.split('_')[1])
    product = Product.objects.get(id=product_id)

    # Поиск продукта в корзине
    cart_item = next((item for item in user_data[user_id]['order']['items'] if item['id'] == product_id), None)

    if cart_item:
        # Если товар есть в корзине, проверяем доступное количество
        if product.quantity - cart_item['quantity'] > 0:
            cart_item['quantity'] += 1
            user_data[user_id]['order']['total_price'] += product.price
            bot.send_message(user_id, f"Еще один {product.name} добавлен в корзину.")
        else:
            bot.send_message(user_id, f"Извините, но {product.name} больше нет в наличии.")
    else:
        # Если товара нет в корзине, добавляем его
        if product.quantity > 0:
            user_data[user_id]['order']['items'].append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': 1
            })
            user_data[user_id]['order']['total_price'] += product.price
            bot.send_message(user_id, f"{product.name} добавлен в корзину.")
        else:
            bot.send_message(user_id, f"Извините, {product.name} закончился.")

    show_order_and_next_steps(user_id)


    user_data[user_id]['order']['total_price'] += product.price
def show_order_and_next_steps(user_id):
    order = user_data[user_id]['order']
    summary_lines = []
    for item in order['items']:
        summary_lines.append(f"{item['name']} x {item['quantity']}: {item['price'] * item['quantity']} руб.")

    summary = "\n".join(summary_lines)
    total_price = sum(item['price'] * item['quantity'] for item in order['items'])

    markup = types.InlineKeyboardMarkup(row_width=2)
    button_add_more_food = types.InlineKeyboardButton("Добавить еще еду", callback_data='select_food')
    button_add_more_drink = types.InlineKeyboardButton("Добавить еще напитки", callback_data='select_drink')
    button_select_sector = types.InlineKeyboardButton("Выбрать место", callback_data='choose_sector')
    button_cancel = types.InlineKeyboardButton("Отменить", callback_data='cancel')
    markup.add(button_add_more_food, button_add_more_drink, button_select_sector, button_cancel)

    bot.send_message(user_id, f"Ваш заказ:\n{summary}\nОбщая сумма: {total_price} руб.\nЧто вы хотите сделать дальше?", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == 'choose_sector')
def select_sector(call):
    print("Выбор сектора запущен")  # Для отладки

    user_id = call.from_user.id  # Правильно извлекаем user_id из call
    markup = types.InlineKeyboardMarkup(row_width=1)
    sectors = ["Ложа D", "Vip Ложа", "PremiumVip", "Семейная Ложа", "Стандартный сектор"]
    for sector in sectors:
        markup.add(types.InlineKeyboardButton(sector, callback_data=f"sector_{sector}"))
    bot.send_message(user_id, "Выберите сектор:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Заказ отменен. Начните заново командой /start.")
    if user_id in user_data:
        del user_data[user_id]
@bot.callback_query_handler(func=lambda call: call.data.startswith('sector_'))
def handle_sector_choice(call):
    user_id = call.from_user.id
    sector = call.data.split('_')[1]
    user_data[user_id]['order']['sector'] = sector
    msg = bot.send_message(user_id, "Введите номер ряда:")
    bot.register_next_step_handler(msg, process_row_input)

def process_row_input(message):
    user_id = message.chat.id
    row = message.text
    if not row.isdigit():
        msg = bot.reply_to(message, "Номер ряда должен быть числом. Пожалуйста, введите номер ряда заново:")
        bot.register_next_step_handler(msg, process_row_input)
        return
    user_data[user_id]['order']['row'] = row
    msg = bot.send_message(user_id, "Введите номер места:")
    bot.register_next_step_handler(msg, process_seat_input)
def process_seat_input(message):
    user_id = message.chat.id
    seat = message.text
    if not seat.isdigit():
        msg = bot.reply_to(message, "Номер места должен быть числом. Пожалуйста, введите номер места заново:")
        bot.register_next_step_handler(msg, process_seat_input)
        return
    user_data[user_id]['order']['seat'] = seat
    confirm_order(user_id)

def confirm_order(user_id):
    order_details = user_data[user_id]['order']
    summary_lines = []
    total_price = Decimal('0.0')  # Обнуляем общую стоимость для нового расчета

    for item in order_details['items']:
        product = Product.objects.get(id=item['id'])
        item_total = item['price'] * item['quantity']
        total_price += item_total  # Добавляем к общей стоимости заказа

        if product.quantity >= item['quantity']:
            product.quantity -= item['quantity']
            product.save()
            summary_lines.append(f"{item['name']} x {item['quantity']}: {item_total} руб.")
        else:
            bot.send_message(user_id, f"К сожалению, {item['name']} закончился и был удален из заказа.")
            total_price -= item_total  # Вычитаем из общей стоимости недоступный товар

    if summary_lines:
        seat_info = f"Сектор: {order_details['sector']}, Ряд: {order_details['row']}, Место: {order_details['seat']}"
        summary = "\n".join(summary_lines + [seat_info])
        bot.send_message(user_id, f"Ваш заказ:\n{summary}\nОбщая сумма: {total_price.quantize(Decimal('1.00'))} руб.")
        
        # Сохранение заказа в базу данных
        Order.objects.create(
            items="\n".join([f"{item['name']}: {item['price']} руб." for item in order_details['items']]),
            total_price=total_price,
            sector=order_details['sector'],
            row=order_details['row'],
            seat=order_details['seat'],
        )
        ensure_user_data_initialized(user_id)  # Очистка данных заказа
    else:
        bot.send_message(user_id, "К сожалению, ни один товар не доступен для заказа.")
        ensure_user_data_initialized(user_id)  # Очистка корзины
class Command(BaseCommand):
    help = 'Runs the telegram bot'

    def handle(self, *args, **options):
        bot.polling()
