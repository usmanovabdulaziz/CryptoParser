import logging
import io
import re
import requests
from dotenv import load_dotenv
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    JobQueue
)
import yfinance as yf
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta
from telegram.request import HTTPXRequest
from telegram.error import TimedOut

load_dotenv()

# Plotly configuration
pio.kaleido.scope.mathjax = None

# Logging configuration
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('BOT_TOKEN')  # Replace with your bot token

# Conversation states
SELECT_ACTION, GET_SYMBOL, SET_ALERT = range(3)

# Supported currencies
SUPPORTED_CURRENCIES = {
    'USD': {'symbol': '$', 'name': 'US Dollar'},
    'EUR': {'symbol': '€', 'name': 'Euro'},
    'UZS': {'symbol': 'soʻm', 'name': 'Uzbekistani Som'},
    'RUB': {'symbol': '₽', 'name': 'Russian Ruble'},
    'GBP': {'symbol': '£', 'name': 'British Pound'},
}

# Main menu keyboard
def main_menu_keyboard():
    return [
        [InlineKeyboardButton("📈 Price", callback_data="price"),
         InlineKeyboardButton("📊 Chart", callback_data="chart")],
        [InlineKeyboardButton("🔔 Set Alert", callback_data="alert"),
         InlineKeyboardButton("💱 Change Currency", callback_data="change_currency")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")]
    ]

# Get exchange rate
async def get_exchange_rate(base_curr='USD', target_curr='UZS'):
    try:
        url = f"https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/{base_curr.lower()}.json"
        response = requests.get(url, timeout=10).json()
        return response[base_curr.lower()][target_curr.lower()]
    except Exception as e:
        logger.error(f"Exchange rate error: {str(e)}")
        return None

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if 'currency' not in context.user_data:
        context.user_data['currency'] = 'USD'

    currency_info = "\n".join(
        f"{code}: {data['name']} ({data['symbol']})"
        for code, data in SUPPORTED_CURRENCIES.items()
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"""📈 **Stock Monitoring Bot**

💱 Supported Currencies (use /currency CODE to change):
{currency_info}

Current currency: {context.user_data['currency']}

Select an option:""",
        reply_markup=InlineKeyboardMarkup(main_menu_keyboard()),
        parse_mode="Markdown"
    )
    return SELECT_ACTION

# Button callback handler
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    context.user_data['action'] = data

    if data == "price":
        await query.edit_message_text(
            "💰 Enter symbol (e.g., AAPL, ^GSPC, BTC-USD):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
        )
        return GET_SYMBOL

    elif data == "chart":
        await query.edit_message_text(
            "📊 Enter symbol for chart (e.g., AAPL, ^GSPC, BTC-USD):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
        )
        return GET_SYMBOL

    elif data == "alert":
        await query.edit_message_text(
            "🔔 Enter symbol and price (e.g., AAPL 150, BTC-USD 60000):",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
        )
        return SET_ALERT

    elif data == "change_currency":
        await query.edit_message_text(
            "💱 Select currency:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("USD $", callback_data="currency_USD"),
                 InlineKeyboardButton("EUR €", callback_data="currency_EUR")],
                [InlineKeyboardButton("UZS soʻm", callback_data="currency_UZS"),
                 InlineKeyboardButton("RUB ₽", callback_data="currency_RUB")],
                [InlineKeyboardButton("GBP £", callback_data="currency_GBP"),
                 InlineKeyboardButton("⬅️ Back", callback_data="back")]
            ])
        )
        return SELECT_ACTION

    elif data == "help":
        await query.edit_message_text(
            "ℹ️ **Help Menu**\n\n"
            "**Available Commands:**\n"
            "/start - Restart the bot\n"
            "/currency CODE - Change currency (e.g., /currency USD)\n"
            "/price SYMBOL - Get price for a symbol (e.g., /price AAPL)\n"
            "/chart SYMBOL - Get chart for a symbol (e.g., /chart BTC-USD)\n"
            "/alert SYMBOL PRICE - Set an alert (e.g., /alert ^GSPC 5000)\n\n"
            "**Symbol Examples:**\n"
            "AAPL - Apple\n"
            "^GSPC - S&P 500\n"
            "BTC-USD - Bitcoin\n"
            "EURUSD=X - Euro/USD\n\n"
            "Alert format: SYMBOL PRICE\nExample: AAPL 150",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
        )
        return SELECT_ACTION

    elif data == "back":
        await query.edit_message_text(
            "📈 **Main Menu**",
            reply_markup=InlineKeyboardMarkup(main_menu_keyboard()),
            parse_mode="Markdown"
        )
        return SELECT_ACTION

    elif data.startswith("currency_"):
        currency = data.split("_")[1]
        context.user_data['currency'] = currency
        await query.edit_message_text(
            f"✅ Currency changed to {SUPPORTED_CURRENCIES[currency]['name']} ({currency})",
            reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
        )
        return SELECT_ACTION

# Get stock data function
async def get_stock_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol = update.message.text.upper()
    action = context.user_data.get('action')

    # Validate symbol format
    if not re.match(r'^[A-Za-z0-9^][A-Za-z0-9-.=^]{0,11}$', symbol):
        await update.message.reply_text(
            "⚠️ Invalid symbol. Use 1-12 characters with letters, numbers, ^, -, ., or = (e.g., AAPL, ^GSPC, BTC-USD)",
            reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
        )
        return SELECT_ACTION

    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1d")

        # Check if symbol exists
        if data.empty:
            await update.message.reply_text(
                f"⚠️ {symbol} not found. Please check the symbol and try again.",
                reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
            )
            return SELECT_ACTION

        # Get user's selected currency
        currency = context.user_data.get('currency', 'USD')
        currency_data = SUPPORTED_CURRENCIES.get(currency, SUPPORTED_CURRENCIES['USD'])

        # Convert prices if not USD
        if currency != 'USD':
            rate = await get_exchange_rate('USD', currency)
            if rate is None:
                await update.message.reply_text(
                    "⚠️ Could not fetch exchange rate. Displaying in USD.",
                    reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
                )
                currency = 'USD'
                currency_data = SUPPORTED_CURRENCIES['USD']
                rate = 1
        else:
            rate = 1

        if action == "price":
            response = f"📊 **{symbol}** ({currency_data['name']})\n"
            response += f"💰 Current Price: {currency_data['symbol']}{data['Close'].iloc[-1] * rate:.2f}\n"
            response += f"📈 High: {currency_data['symbol']}{data['High'].max() * rate:.2f}\n"
            response += f"📉 Low: {currency_data['symbol']}{data['Low'].min() * rate:.2f}\n"
            if 'Volume' in data.columns and not data['Volume'].isna().all():
                response += f"🔄 Volume: {int(data['Volume'].iloc[-1]):,}\n"
            await update.message.reply_text(response, parse_mode="Markdown")

        elif action == "chart":
            try:
                fig = go.Figure(data=[go.Candlestick(
                    x=stock.history(period="1mo").index,
                    open=stock.history(period="1mo")['Open'],
                    high=stock.history(period="1mo")['High'],
                    low=stock.history(period="1mo")['Low'],
                    close=stock.history(period="1mo")['Close']
                )])
                fig.update_layout(
                    title=f"{symbol} - 1 Month Price ({currency})",
                    xaxis_rangeslider_visible=False
                )
                img_bytes = fig.to_image(format="png", engine="kaleido")
                await update.message.reply_photo(
                    photo=io.BytesIO(img_bytes),
                    caption=f"📈 {symbol} Price Chart ({currency})"
                )
            except Exception as e:
                logger.error(f"Chart error: {str(e)}")
                await update.message.reply_text(
                    "⚠️ Error generating chart. Please try again.",
                    reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
                )
                return SELECT_ACTION

        await update.message.reply_text(
            "Select another option:",
            reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
        )
        return SELECT_ACTION

    except Exception as e:
        logger.error(f"Data fetch error: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error fetching data. Please try again.",
            reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
        )
        return SELECT_ACTION

# Set alert function
async def set_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.upper().split()
        if len(parts) != 2:
            await update.message.reply_text(
                "⚠️ Invalid format! Use: SYMBOL PRICE\nExample: AAPL 150",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
            )
            return SET_ALERT

        symbol, price_str = parts[0], parts[1]

        # Validate symbol
        if not re.match(r'^[A-Za-z0-9^][A-Za-z0-9-.=^]{0,11}$', symbol):
            await update.message.reply_text(
                "⚠️ Invalid symbol. Use 1-12 characters with letters, numbers, ^, -, ., or = (e.g., AAPL, ^GSPC, BTC-USD)",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
            )
            return SET_ALERT

        # Validate price
        try:
            price = float(price_str)
        except ValueError:
            await update.message.reply_text(
                "⚠️ Invalid price! Enter a valid number",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
            )
            return SET_ALERT

        # Verify symbol exists
        stock = yf.Ticker(symbol)
        if stock.history(period="1d").empty:
            await update.message.reply_text(
                f"⚠️ {symbol} not found. Please check the symbol.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
            )
            return SET_ALERT

        # Get user's currency
        currency = context.user_data.get('currency', 'USD')
        currency_data = SUPPORTED_CURRENCIES.get(currency, SUPPORTED_CURRENCIES['USD'])

        # Save alert (in USD for consistency)
        if 'alerts' not in context.bot_data:
            context.bot_data['alerts'] = {}

        context.bot_data['alerts'][update.effective_user.id] = {
            'symbol': symbol,
            'target_price': price,
            'currency': currency,
            'chat_id': update.effective_chat.id
        }

        await update.message.reply_text(
            f"✅ Alert set for {symbol} at {currency_data['symbol']}{price:.2f} ({currency})",
            reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
        )
        return SELECT_ACTION

    except Exception as e:
        logger.error(f"Alert error: {str(e)}")
        await update.message.reply_text(
            "⚠️ Error setting alert. Please try again.",
            reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
        )
        return SET_ALERT

# Check alerts function
async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    if 'alerts' not in context.bot_data:
        return

    for user_id, alert_data in list(context.bot_data['alerts'].items()):
        symbol = alert_data.get('symbol')
        target_price = alert_data.get('target_price')
        currency = alert_data.get('currency', 'USD')
        chat_id = alert_data.get('chat_id')

        if not all([symbol, target_price, chat_id]):
            continue

        try:
            current_data = yf.Ticker(symbol).history(period="1d")
            if current_data.empty:
                continue

            current_price = current_data['Close'].iloc[-1]

            # Convert target price to USD if needed
            if currency != 'USD':
                rate = await get_exchange_rate('USD', currency)
                if rate is None:
                    continue
                target_price_usd = target_price / rate
            else:
                target_price_usd = target_price

            if current_price <= target_price_usd:
                currency_data = SUPPORTED_CURRENCIES.get(currency, SUPPORTED_CURRENCIES['USD'])
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🚨 {symbol} price reached {currency_data['symbol']}{target_price:.2f}!\n"
                         f"Current price: {currency_data['symbol']}{current_price * (1 / rate if currency != 'USD' else 1):.2f} ({currency})"
                )
                del context.bot_data['alerts'][user_id]

        except Exception as e:
            logger.error(f"Alert check error for {user_id}: {str(e)}")
            continue

# Error handler with improved feedback
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="An exception occurred:", exc_info=context.error)

    # Check if the error is a timeout
    if isinstance(context.error, TimedOut):
        error_message = "⚠️ Connection timed out. Please check your internet connection and try again."
    else:
        error_message = "⚠️ An unexpected error occurred. Please try again later."

    if update.message:
        await update.message.reply_text(
            error_message,
            reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
        )
    elif update.callback_query:
        await update.callback_query.message.reply_text(
            error_message,
            reply_markup=InlineKeyboardMarkup(main_menu_keyboard())
        )
    return SELECT_ACTION

# Main function with custom request settings
def main():
    # Configure HTTPXRequest with increased timeout
    request = HTTPXRequest(
        connection_pool_size=10,
        http_version="1.1",
        connect_timeout=30,  # Increased from default 5s to 30s
        read_timeout=30      # Increased from default 5s to 30s
    )

    application = Application.builder().token(TOKEN).request(request).build()

    # Set up job queue for alert checking
    job_queue = application.job_queue
    job_queue.run_repeating(check_alerts, interval=300.0, first=10.0)

    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_ACTION: [CallbackQueryHandler(handle_button)],
            GET_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_stock_data)],
            SET_ALERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_alert)]
        },
        fallbacks=[CommandHandler('start', start)],
    )

    application.add_handler(conv_handler)
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()