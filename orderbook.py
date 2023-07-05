import websocket
import json
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

TELEGRAM_TOKEN = 'YOUR_TELEGRAM_TOKEN'
CHAT_ID = 'YOUR_CHAT_ID'

bot = Bot(token=TELEGRAM_TOKEN)
updater = Updater(token=TELEGRAM_TOKEN)
dispatcher = updater.dispatcher

def group_orders(orders, group_size):
    result = {}
    for order in orders:
        price = float(order[0])
        quantity = float(order[1])
        group = int(price / group_size) * group_size
        if group not in result:
            result[group] = 0
        result[group] += quantity
    return result

def send_orderbook(update: Update, context: CallbackContext):
    data = context.bot_data.get('orderbook')
    if not data:
        update.callback_query.answer(text='No data available')
        return

    bids = data['b']
    asks = data['a']

    grouped_bids = group_orders(bids, 100)
    grouped_asks = group_orders(asks, 100)

    message = 'asks\n'
    for price, quantity in grouped_asks.items():
        message += f'{price} {quantity}\n'

    message += '\nbids\n'
    for price, quantity in grouped_bids.items():
        message += f'{price} {quantity}\n'

    update.callback_query.answer()
    update.callback_query.message.reply_text(message)

def on_message(ws, message):
    data = json.loads(message)
    dispatcher.bot_data['orderbook'] = data

def on_error(ws, error):
    print(error)

def on_close(ws):
    print('### closed ###')

def on_open(ws):
    print('### connected ###')

def start(update: Update, context: CallbackContext):
    keyboard = [[InlineKeyboardButton('Show Orderbook with +100 BTC', callback_data='orderbook')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)

if __name__ == '__main__':
    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    orderbook_handler = CallbackQueryHandler(send_orderbook, pattern='orderbook')
    dispatcher.add_handler(orderbook_handler)

    updater.start_polling()

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp('wss://stream.binance.com:9443/ws/btcusdt@depth',
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open
    ws.run_forever()
