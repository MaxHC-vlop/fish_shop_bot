import logging
import enum

from textwrap import dedent

import elastic_cms

import telegram
import redis

from environs import Env
from telegram.ext import CommandHandler, MessageHandler
from telegram.ext import CallbackContext, CallbackQueryHandler
from telegram.ext import Filters, Updater, ConversationHandler
from telegram import ReplyKeyboardMarkup, Update
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram import ReplyKeyboardRemove


logger = logging.getLogger(__file__)


class UserStatus(enum.Enum):
    HANDLE_MENU = 0
    HANDLE_DESCRIPTION = 1
    HANDLE_CART=2


user_status = UserStatus(value=True)


def button(update: Update, context: CallbackContext) -> None:
    database = context.bot_data['redis_session']
    access_token = database.get('access_token')
    query = update.callback_query
    query.answer()

    database.set('product_id', query.data)
    product_detail = elastic_cms.get_product_detail(access_token, query.data)
    file_id = elastic_cms.get_file_id(access_token, query.data)
    link = elastic_cms.get_image_link(access_token, file_id)

    numbers = [1, 5, 10]
    keyboard = [
        [InlineKeyboardButton(f'{number}кг', callback_data=number)
        for number in numbers],
        [InlineKeyboardButton('Меню', callback_data='menu')],
        [InlineKeyboardButton('Корзина', callback_data='cart')]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.delete()

    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=link,
        caption=product_detail,
        reply_markup=reply_markup
    )

    return user_status.HANDLE_MENU


def menu(update: Update, context: CallbackContext) -> None:
    database = context.bot_data['redis_session']
    products = database.hgetall('products')
    message = 'Please choose:'

    query = update.callback_query

    keyboard = [
        [InlineKeyboardButton(name, callback_data=id)]
        for name, id in products.items()
    ]
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        query.answer()
        query.message.delete()

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=reply_markup
    )

    return user_status.HANDLE_DESCRIPTION


def added_product_to_cart(update: Update, context: CallbackContext):
    database = context.bot_data['redis_session']
    access_token = database.get('access_token')
    product_id = database.get('product_id')
    user_id = update.effective_user.id

    query = update.callback_query
    query.answer()
    quanity = int(query.data)
    elastic_cms.add_product_to_cart(access_token, user_id, product_id, quanity)

    return user_status.HANDLE_MENU


def show_cart(update: Update, context: CallbackContext):
    database = context.bot_data['redis_session']
    access_token = database.get('access_token')
    cart_id = update.effective_user.id

    cart_info = elastic_cms.get_cart(access_token, cart_id)
    message = elastic_cms.formated_message(cart_info)
    products_in_cart = cart_info['products']

    button = 'Убрать {name}'
    keyboard = [
        [InlineKeyboardButton(
            button.format_map(items), callback_data=product_id
        )]
        for product_id, items in products_in_cart.items()
    ]
    keyboard += [
        [InlineKeyboardButton('Меню', callback_data='menu')],
        [InlineKeyboardButton('Оплатить', callback_data='pay')]
    ]

    query = update.callback_query
    query.answer()
    query.message.delete()

    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=message,
        reply_markup=reply_markup
    )

    return user_status.HANDLE_CART


def remove_product(update: Update, context: CallbackContext):
    database = context.bot_data['redis_session']
    access_token = database.get('access_token')
    cart_id = update.effective_user.id

    query = update.callback_query
    query.answer()
    product_id = query.data

    elastic_cms.remove_item_from_cart(access_token, cart_id, product_id)

    return show_cart(update, context)


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Счастливо! До новых встреч!',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    env = Env()
    env.read_env()
    token = env.str('TG_TOKEN')
    database_password = env.str('REDIS_DATABASE_PASSWORD')
    database_host = env.str('REDIS_DATABASE_HOST')
    database_port = env.int('REDIS_DATABASE_PORT')
    client_id = env.str('CLIENT_ID')
    client_secret = env.str('CLIENT_TOKEN')

    database = redis.Redis(
        host=database_host,
        port=database_port,
        password=database_password,
        db=0,
        decode_responses=True
    )

    access_token = elastic_cms.fetch_access_token(client_id, client_secret)
    products = elastic_cms.get_all_products(access_token)

    database.set('access_token', access_token)
    database.hset('products', mapping=products)

    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.bot_data['redis_session'] = database

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', menu)],
        states={
            user_status.HANDLE_DESCRIPTION: [
                CallbackQueryHandler(button, pattern=r'[A-Za-z\d-]{36}'),
                CallbackQueryHandler(show_cart, pattern=r'cart'),
            ],
            user_status.HANDLE_MENU: [
                CallbackQueryHandler(menu, pattern=r'menu'),
                CallbackQueryHandler(added_product_to_cart, pattern=r'\d{1,2}'),
                CallbackQueryHandler(show_cart, pattern=r'cart'),
            ],
            user_status.HANDLE_CART: [
                CallbackQueryHandler(menu, pattern=r'menu'),
                CallbackQueryHandler(remove_product, pattern=r'[A-Za-z\d-]{36}'),
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_message=False
    )
    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
