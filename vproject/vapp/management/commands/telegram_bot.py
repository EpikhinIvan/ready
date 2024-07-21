from django.core.management.base import BaseCommand
from telebot import TeleBot, types
from telebot.types import Message, CallbackQuery
from vapp.models import Product, Order, Chat, BotStatus, Helper
from django.db import transaction
from decimal import Decimal
from functools import wraps
import uuid
from datetime import datetime
import hashlib

ADMIN_TELEGRAM_ID = 865127428

bot = TeleBot('6014766028:AAGQtwWJuFpOFvDeEYGKlzzPgc2gZAMJkfc')


# функция обертка для проверки статуса
def check_bot_status(func):
    @wraps(func)
    def wrapper(call_or_message):
        status = BotStatus.objects.get(id=1).is_active
        if not status:
            if isinstance(call_or_message, Message):
                bot.reply_to(call_or_message, "Бот еще не начал свою работу, попробуйте позже")
            elif isinstance(call_or_message, CallbackQuery):
                bot.answer_callback_query(call_or_message.id, "Бот еще не начал свою работу, попробуйте позже")
        else:
            return func(call_or_message)
    return wrapper

user_data = {}

# инициализация данных пользователя в user_data 
def ensure_user_data_initialized(user_id):
        user_data[user_id] = {
            'order': {
                'items': [],
                'total_price': Decimal('0.00'),
                'sector': None,
                'row': None,
                'seat': None
            }
        }
       
       
# команда хелп
@bot.message_handler(commands=['help'])
def start_order(message):
    chat_id = message.chat.id
    helper_instance = Helper.objects.last()
    if helper_instance:
        telegram_username = helper_instance.telegram_username
        bot.send_message(chat_id, f'По любым вопросам можете обращаться @{telegram_username}')
    else:
        bot.send_message(chat_id, 'Не удалось получить информацию о пользователе Telegram')


# команда старт
@bot.message_handler(commands=['start'])
@check_bot_status
def start_order(message):
    chat_id = message.chat.id
    Chat.objects.get_or_create(chat_id=str(chat_id))
    username = message.from_user.username
    first_name = message.from_user.first_name
    user_id = message.chat.id
    bot.send_message(user_id, "Добро пожаловать на стадион! У нас есть разнообразные комбо-предложения, в каждое из которых входит напиток на твой выбор.")

    Chat.objects.update_or_create(chat_id=str(chat_id), defaults={'username': username, 'first_name': first_name})

    ensure_user_data_initialized(user_id)
    select_product_category_direct(user_id, 'FOOD')


#FOOD
def select_product_category_direct(user_id, category):
    products = Product.objects.filter(category=category, quantity__gt=0).values('id', 'name', 'price')
    markup = types.InlineKeyboardMarkup(row_width=1)
    for product in products:
        button_text = f"{product['name']} - {product['price']} тенге"  
        button = types.InlineKeyboardButton(button_text, callback_data=f"product_{product['id']}")
        markup.add(button)
    back_button = types.InlineKeyboardButton("Назад", callback_data="back_to_start")
    bot.send_message(user_id, f"Выберите {category}:", reply_markup=markup)


# назад кнопка
@bot.callback_query_handler(func=lambda call: call.data == "back_to_categories")
@check_bot_status


# обработчик колбека с продукт_
@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
@check_bot_status
def add_product_to_order(call):
    user_id = call.from_user.id
    product_id = int(call.data.split('_')[1])
    product = Product.objects.get(id=product_id)

    # Поиск продукта в корзине
    cart_item = None
    for item in user_data.get(user_id, {}).get('order', {}).get('items', []):
        if item.get('id') == product_id:
            cart_item = item
            break

    # Обновление корзины или добавление нового товара
    if cart_item:
        if product.quantity - cart_item['quantity'] > 0:
            cart_item['quantity'] += 1
            # user_data[user_id]['order']['total_price'] += product.price
            bot.send_message(user_id, f"Вы добавили {product.name} в корзину.")
        else:
            bot.send_message(user_id, f"Извините, но {product.name} больше нет в наличии.")
    else:
        if product.quantity > 0:
            user_data.setdefault(user_id, {}).setdefault('order', {}).setdefault('items', []).append({
                'id': product.id,
                'name': product.name,
                'price': product.price,
                'quantity': 1
            })
            # user_data[user_id]['order']['total_price'] += product.price
            bot.send_message(user_id, f"{product.name} добавлен в корзину.")
        else:
            bot.send_message(user_id, f"Извините, {product.name} закончился.")

    if product.category == 'FOOD':
        select_product_category_direct(user_id, 'DRINK')
    else:
        show_order_and_next_steps(user_id)

    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")

    
# после выбора вылазит весь заказ
def show_order_and_next_steps(user_id,):
    order = user_data[user_id]['order']
    summary_lines = []
    for item in order['items']:
        summary_lines.append(f"{item['name']} x {item['quantity']}: {item['price'] * item['quantity']} тг.")

    summary = "\n".join(summary_lines)
    total_price = sum(item['price'] * item['quantity'] for item in order['items'])

    markup = types.InlineKeyboardMarkup(row_width=2)
    button_select_sector = types.InlineKeyboardButton("Выбрать место", callback_data='choose_sector')
    # button_add_more_food = types.InlineKeyboardButton("Заказать еще", callback_data='add_more')
    button_cancel = types.InlineKeyboardButton("Отменить", callback_data='cancel')
    # markup.add(button_select_sector, button_cancel, button_add_more_food)
    markup.add(button_select_sector, button_cancel)


    bot.send_message(user_id, f"Ваш заказ:\n{summary}\nОбщая сумма: {total_price} тг.\n\nЧто вы хотите сделать дальше?", reply_markup=markup)
    

# добавить еще колбек обработчик
@bot.callback_query_handler(func=lambda call: call.data == 'add_more')
@check_bot_status
def handle_add_more(call):
    user_id = call.from_user.id
    select_product_category_direct(user_id, 'FOOD')


# колбек обработчик выбора сектора
@bot.callback_query_handler(func=lambda call: call.data == 'choose_sector')
@check_bot_status
def select_sector(call):
    user_id = call.from_user.id
    order = user_data[user_id]['order']

    total_price = sum(item['price'] * item['quantity'] for item in order['items'])

    if total_price >= Decimal('249.00'):
        markup = types.InlineKeyboardMarkup(row_width=1)
        sectors = ["Ложа D", "Vip Ложа", "PremiumVip", "Семейная Ложа", "Стандартный сектор"]
        for sector in sectors:
            markup.add(types.InlineKeyboardButton(sector, callback_data=f"sector_{sector}"))
        bot.send_message(user_id, "Выберите сектор:", reply_markup=markup)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    else:
        bot.send_message(user_id, "Минимальная сумма заказа должна быть 1500 тг. Пожалуйста, добавьте больше продуктов.")


# обработчки отмены заказа
@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
@check_bot_status
def cancel(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Заказ отменен. Начните заново командой /start.")
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Заказ отменен.", reply_markup=None)

    if user_id in user_data:
        del user_data[user_id]

# колбек обработчик выбранного места
@bot.callback_query_handler(func=lambda call: call.data.startswith('sector_'))
@check_bot_status
def handle_sector_choice(call):
    user_id = call.from_user.id
    sector = call.data.split('_')[1]
    user_data[user_id]['order']['sector'] = sector
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали {sector}.", reply_markup=None)

    msg = bot.send_message(user_id, "Введите сектор-ряд в формате 'Сектор-Ряд', например '0-10': ")
    bot.register_next_step_handler(msg, process_sector_row_input)


def process_sector_row_input(message):
    user_id = message.chat.id
    input_text = message.text.strip().upper()  # Преобразуем текст в верхний регистр для единообразия
    
    try:
        sector_row = input_text.split('-')
        if len(sector_row) != 2:
            raise ValueError("Неверный формат. Введите сектор-ряд в формате 'Сектор-Ряд', например '0-10'.")
        
        sector = sector_row[0].strip()
        row = sector_row[1].strip()
        
        user_data[user_id]['order']['row'] = f"{sector}-{row}"
        
        # Запрашиваем номер места
        msg = bot.send_message(user_id, "Введите номер места:")
        bot.register_next_step_handler(msg, process_seat_input)
    
    except ValueError as e:
        msg = bot.reply_to(message, f"{e} Пожалуйста, введите сектор-ряд в формате 'Сектор-Ряд', например '0-10':")
        bot.register_next_step_handler(msg, process_sector_row_input)

def process_seat_input(message):
    user_id = message.chat.id
    seat = message.text
    if not seat.isdigit():
        msg = bot.reply_to(message, "Номер места должен быть числом. Пожалуйста, введите номер места заново:")
        bot.register_next_step_handler(msg, process_seat_input)
        return
    user_data[user_id]['order']['seat'] = seat
    confirm_order(user_id)



# генерация уникального номера заказа
def generate_unique_order_number():
    random_uuid = uuid.uuid4()
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    raw_order_number = str(random_uuid) + current_time
    hash_object = hashlib.sha256(raw_order_number.encode())
    order_number = hash_object.hexdigest()[:6].upper()
    return order_number

# конец заказа
def confirm_order(user_id):
    order_number = generate_unique_order_number()
    order_details = user_data[user_id]['order']
    
    summary_lines = []

    total_price = sum(Decimal(str(item['price'])) * item['quantity'] for item in order_details['items'])

    for item in order_details['items']:
        product = Product.objects.get(id=item['id'])
        if product.quantity >= item['quantity']:
            product.quantity -= item['quantity']
            product.save()
            summary_lines.append(f"{item['name']} x {item['quantity']}: {Decimal(str(item['price'])) * item['quantity']} тг.")
        else:
            bot.send_message(user_id, f"К сожалению, {item['name']} недоступен.")

    if summary_lines:
        seat_info = f"Ложа: {order_details['sector']}, Сектор-Ряд: {order_details['row']}, Место: {order_details['seat']}"
        summary = "\n".join(summary_lines + [seat_info])
        bot.send_message(user_id, f"Ваш заказ:\n{summary}\nОбщая сумма: {total_price.quantize(Decimal('1.00'))} тг.")

        # Отправка сообщения с заказом в другой чат с кнопкой "новые заказы"
        other_chat_id = '-1002134064826'
        # other_chat_id = '-4233254678'

        keyboard = types.InlineKeyboardMarkup()
        callback_button = types.InlineKeyboardButton(text="Оплачено", callback_data=f"paid_{order_number}")
        keyboard.add(callback_button)
        bot.send_message(other_chat_id, f"Заказ:{order_number}\n{summary}\nОбщая сумма: {total_price.quantize(Decimal('1.00'))} тг.", reply_markup=keyboard)


        payment_message = f"Ваш заказ получен. Для оплаты воспользуйтесь номером Каспи: +77006755125 (Иван Е.). \n\n!!Обязательно!! прикрепите номер заказа в комментарии.\n\nНомер заказа: ({order_number})\n\n После потдверждения оплаты, ожидайте заказ в течении 10-15минут\n\n Чтобы заказать заново, воспользуйтесь командой /start"
        bot.send_message(user_id, payment_message)

        items_description = "\n".join([f"{item['name']} x {item['quantity']}" for item in order_details['items']])
        
        Order.objects.create(
            userid = user_id,
            order_number=order_number,
            items=items_description,
            total_price=total_price.quantize(Decimal('1.00')),
            sector=order_details['sector'],
            row=order_details['row'],
            seat=order_details['seat'],
        )
        ensure_user_data_initialized(user_id)
    else:
        bot.send_message(user_id, "К сожалению, ни один товар не доступен для заказа.")
        ensure_user_data_initialized(user_id)



# Обработчик нажатия кнопки "Оплачено"
@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def handle_paid_callback(callback_query):
    bot.answer_callback_query(callback_query.id)
    order_number = callback_query.data.split('_')[1]
    with transaction.atomic():
        order = Order.objects.select_for_update().filter(order_number=order_number).first()
        if order:
            order.mark_as_paid()
            message_text = f"Статус заказа {order_number} изменен на оплачено."
            bot.edit_message_text(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id,  text=message_text)
            # send_order_info_to_chat(order, -4200084248)
            send_order_info_to_chat(order, -1002190584049)



def send_order_info_to_chat(order, chat_id):
    order_details = f"Номер заказа: {order.order_number}\nКорзина: {order.items}\nОбщая сумма: {order.total_price} тг.\nЛожа: {order.sector}, Сектор-Ряд: {order.row}, Место: {order.seat}"
    bot.send_message(chat_id, order_details)




# обработчик фотки
@bot.message_handler(content_types='photo')
def get_photo(message):
    bot.send_message(message.chat.id, 'У меня нет возможности просматривать фото :(')

# обработчик не нужного текста
@bot.message_handler(content_types='text')
def get_photo(message):
    bot.send_message(message.chat.id, 'Простите, я не умею читать :(')


class Command(BaseCommand):
    help = 'Runs the telegram bot'

    def handle(self, *args, **options):
        bot.polling()