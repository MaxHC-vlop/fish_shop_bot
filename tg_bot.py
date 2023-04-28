import logging

from elastic_cms import (fetch_access_token, get_all_products, get_product_detail, get_file_id, get_image_link)

from textwrap import dedent

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


def start(update: Update, context: CallbackContext) -> None:
    database = context.bot_data['redis_session']
    products = database.hgetall('products')
    message = 'Please choose:'
    keyboard = [
        [InlineKeyboardButton(name, callback_data=id)]
        for name, id in products.items()
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    update.message.reply_text(message, reply_markup=reply_markup)


def button(update: Update, context: CallbackContext) -> None:
    database = context.bot_data['redis_session']
    access_token = database.get('access_token')
    query = update.callback_query
    query.answer()
    product_detail = get_product_detail(access_token, query.data)
    file_id = get_file_id(access_token, query.data)
    link = get_image_link(access_token, file_id)

    query.message.delete()

    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=link,
        caption=product_detail
    )


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text(
        'Счастливо! До новых встреч!',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def elastic_cms():
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

    access_token = fetch_access_token(client_id, client_secret)
    products = get_all_products(access_token)

    database.set('access_token', access_token)
    database.hset('products', mapping=products)

    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.bot_data['redis_session'] = database

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('cancel', cancel))
    dispatcher.add_handler(CallbackQueryHandler(button))
    updater.start_polling()


if __name__ == '__main__':
    elastic_cms()
