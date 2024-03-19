from django.core.management.base import BaseCommand
from telebot import TeleBot, types
from django.db.models import F
from vapp.models import Product
from decimal import Decimal
from vapp.models import Order
from vapp.models import Chat
from vapp.models import BotStatus
from functools import wraps
from telebot.types import Message, CallbackQuery

##ТАМ НУЖНО ЦЕНЫ С РУБЛЕЙ НА ТЭЕНГЕ ПОМЕНЯТЬ


##СЮДА СВОЙ АЙПИ МОЖЕШЬ ДОБАВИТЬ НА ВСЯКИЙ
ADMIN_TELEGRAM_ID = 865127428
bot = TeleBot('7171828502:AAHfKBNkG1zTgNtf79YCViNBCOKECvgGqTM')
PAYMENTS_PROVIDER_TOKEN = '5420394252:TEST:543267'


##ПРОВЕРЯЕТ СТАТУС БОТА ПРИ КАААЖДДМОМ ДЕЙСТВИИ
def check_bot_status(func):
    @wraps(func)
    def wrapper(call_or_message):
        status = BotStatus.objects.get(id=1).is_active
        if not status:
            if isinstance(call_or_message, Message):
                bot.reply_to(call_or_message, "Бот временно не работает.")
            elif isinstance(call_or_message, CallbackQuery):
                bot.answer_callback_query(call_or_message.id, "Бот временно не работает.")
        else:
            return func(call_or_message)
    return wrapper

user_data = {}

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
@bot.message_handler(commands=['start'])
@check_bot_status

def start_order(message):
    chat_id = message.chat.id
    Chat.objects.get_or_create(chat_id=str(chat_id))
    chat_id = message.chat.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    user_id = message.chat.id

    # Создание или обновление записи в модели Chat
    Chat.objects.update_or_create(chat_id=str(chat_id), defaults={'username': username, 'first_name': first_name})


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
@check_bot_status

def select_product_category(call):
    user_id = call.from_user.id
    category = call.data.split('_')[1].upper()
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    # Добавление 'price' в список извлекаемых полей
    products = Product.objects.filter(category=category).values('id', 'name', 'price')
    markup = types.InlineKeyboardMarkup(row_width=1)
    for product in products:
        # Формирование текста кнопки с указанием цены продукта
        button_text = f"{product['name']} - {product['price']} руб."
        button = types.InlineKeyboardButton(button_text, callback_data=f"product_{product['id']}")
        markup.add(button)
    back_button = types.InlineKeyboardButton("Назад", callback_data="back_to_categories")
    markup.add(back_button)
    bot.send_message(user_id, f"Выберите {category.lower()}:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "back_to_categories")
@check_bot_status

def back_to_categories(call):
    user_id = call.from_user.id
    show_categories(user_id)  # Показываем снова список категорий
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)



@bot.callback_query_handler(func=lambda call: call.data.startswith('product_'))
@check_bot_status

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
    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None)

    except Exception as e:
        print(f"Ошибка при удалении сообщения: {e}")
    show_order_and_next_steps(user_id)


    user_data[user_id]['order']['total_price'] += product.price
def show_order_and_next_steps(user_id,):
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
@check_bot_status

def select_sector(call):
    user_id = call.from_user.id
    order = user_data[user_id]['order']

    total_price = sum(item['price'] * item['quantity'] for item in order['items'])

    if total_price >= Decimal('1500.00'):
        markup = types.InlineKeyboardMarkup(row_width=1)
        sectors = ["Ложа D", "Vip Ложа", "PremiumVip", "Семейная Ложа", "Стандартный сектор"]
        for sector in sectors:
            markup.add(types.InlineKeyboardButton(sector, callback_data=f"sector_{sector}"))
        bot.send_message(user_id, "Выберите сектор:", reply_markup=markup)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    else:
        bot.send_message(user_id, "Минимальная сумма заказа должна быть 1500 руб. Пожалуйста, добавьте больше продуктов.")
        show_categories(user_id)  # Повторное предложение выбора категории товаров


        
@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
@check_bot_status

def cancel(call):
    user_id = call.from_user.id
    bot.send_message(user_id, "Заказ отменен. Начните заново командой /start.")
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Заказ отменен.", reply_markup=None)

    if user_id in user_data:
        del user_data[user_id]
@bot.callback_query_handler(func=lambda call: call.data.startswith('sector_'))
@check_bot_status

def handle_sector_choice(call):
    user_id = call.from_user.id
    sector = call.data.split('_')[1]
    user_data[user_id]['order']['sector'] = sector
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"Вы выбрали {sector}.", reply_markup=None)

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
    show_order_summary(user_id)

@bot.callback_query_handler(func=lambda call: call.data == 'show_order_summary')
@check_bot_status

def show_order_summary(user_id):
    order_details = user_data[user_id]['order']
    summary_lines = []
    total_price = sum(Decimal(str(item['price'])) * item['quantity'] for item in order_details['items'])

    for item in order_details['items']:
        summary_lines.append(f"{item['name']} x {item['quantity']}: {item['price'] * item['quantity']} руб.")

    summary = "\n".join(summary_lines)
    message_text = f"Ваш заказ:\n{summary}\nОбщая сумма: {total_price.quantize(Decimal('1.00'))} руб.\n\nПодтвердите ваш заказ."

    markup = types.InlineKeyboardMarkup(row_width=1)
    confirm_button = types.InlineKeyboardButton("Подтвердить заказ", callback_data='pay') ##ЗДЕСЬ
    cancel_button = types.InlineKeyboardButton("Отменить", callback_data='cancel')
    markup.add(confirm_button, cancel_button)

    bot.send_message(user_id, message_text, reply_markup=markup)

##ЗДЕСЬ
@bot.callback_query_handler(func=lambda call: call.data == 'pay')
def initiate_payment(call):
    user_id = call.from_user.id  # Получаем ID пользователя из колбэка
    total_price = user_data[user_id]['order']['total_price']  # Получаем общую сумму заказа

    # Переводим общую сумму заказа в копейки и создаем объект цены
    prices = [types.LabeledPrice(label="Общая сумма заказа", amount=int(total_price * 100))]

    # Отправляем инвойс (счет на оплату)
    bot.send_invoice(
    chat_id=call.from_user.id,
    title="Оплата заказа",
    description="Оплата за ваш заказ",
    provider_token=PAYMENTS_PROVIDER_TOKEN,
    currency='KZT',
    prices=prices,
    start_parameter="create_invoice",
    invoice_payload="Unique_Payment_Identifier"  # Уникальный идентификатор платежа
)

# Обработчик успешной оплаты
@bot.message_handler(content_types=['successful_payment'])
def handle_payment(message):
    user_id = message.chat.id
    # После успешной оплаты, можно обновить статус заказа, активировать подписку или предоставить доступ к услугам
    bot.send_message(chat_id=user_id, text="Спасибо за вашу оплату! Ваш заказ будет обработан.")

# Не забудьте обработать pre_checkout_query, чтобы подтвердить оплату
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query_id=pre_checkout_query.id, ok=True, 
                                  error_message="Oops, что-то пошло не так... Пожалуйста, попробуйте еще раз позже.")


#ДОСЮДА


@bot.callback_query_handler(func=lambda call: call.data == 'confirm_order')
def confirm_order(call):
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)

    user_id = call.from_user.id  # Получаем user_id из колбэка

    order_details = user_data[user_id]['order']
    summary_lines = []

    # Подсчет общей суммы заказа производится один раз
    total_price = sum(Decimal(str(item['price'])) * item['quantity'] for item in order_details['items'])

    for item in order_details['items']:
        product = Product.objects.get(id=item['id'])

        if product.quantity >= item['quantity']:
            product.quantity -= item['quantity']
            product.save()
            summary_lines.append(f"{item['name']} x {item['quantity']}: {Decimal(str(item['price'])) * item['quantity']} руб.")
        else:
            bot.send_message(user_id, f"К сожалению, {item['name']} недоступен.")

    if summary_lines:
        seat_info = f"Сектор: {order_details['sector']}, Ряд: {order_details['row']}, Место: {order_details['seat']}"
        summary = "\n".join(summary_lines + [seat_info])
        bot.send_message(user_id, f"Ваш заказ:\n{summary}\nОбщая сумма: {total_price.quantize(Decimal('1.00'))} руб.")

        items_description = "\n".join([f"{item['name']} x {item['quantity']}" for item in order_details['items']])
        
        # Сохранение заказа в базу данных
        Order.objects.create(
            items=items_description,
            total_price=total_price.quantize(Decimal('1.00')),  # Убедитесь, что здесь правильно передается общая сумма
            sector=order_details['sector'],
            row=order_details['row'],
            seat=order_details['seat'],
        )
        ensure_user_data_initialized(user_id)
    else:
        bot.send_message(user_id, "К сожалению, ни один товар не доступен для заказа.")
        ensure_user_data_initialized(user_id)


#Отправка сообщений пользователям, там указан только мой телеграм id, можно добавить свой в самом начале,
         # /broadcast (сообщение) НУ ВООБЩЕ УДАЛИТЬ МОЖНО ЭТУ ФУНКЦИЮ





@bot.message_handler(commands=['broadcast'])
def send_broadcast_message(message):
    if message.from_user.id == ADMIN_TELEGRAM_ID:
        command, *text = message.text.split(maxsplit=1)
        broadcast_message = text[0] if text else "Тестовое сообщение"

        chats = Chat.objects.all()
        for chat in chats:
            try:
                bot.send_message(chat.chat_id, broadcast_message)
            except Exception as e:
                print(f"Не удалось отправить сообщение в чат {chat.chat_id}: {str(e)}")
        bot.reply_to(message, "Сообщение отправлено всем пользователям.")
    else:
        bot.reply_to(message, "У вас нет прав для выполнения этой команды.")

class Command(BaseCommand):
    help = 'Runs the telegram bot'

    def handle(self, *args, **options):
        bot.polling()
