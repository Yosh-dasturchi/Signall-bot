import os
import asyncio
import requests
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔐 ENV VARS (Render)
TOKEN = os.environ.get("BOT_TOKEN")
API_KEY = os.environ.get("API_KEY")
SYMBOL = "XAU/USD"

running = False


# ---------------- WEB SERVER (Render fix) ----------------
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


# ---------------- DATA ----------------
def get_prices():
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval=5min&outputsize=100&apikey={API_KEY}"
        r = requests.get(url, timeout=10).json()

        if "values" not in r:
            return None

        prices = [float(i["close"]) for i in r["values"]]
        prices.reverse()

        return prices if len(prices) >= 30 else None

    except:
        return None


# ---------------- INDICATORS ----------------
def ema(prices, n):
    k = 2 / (n + 1)
    out = [prices[0]]
    for p in prices[1:]:
        out.append(p * k + out[-1] * (1 - k))
    return out


def rsi(prices, period=14):
    gains, losses = [], []

    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(prices):
    tr = [abs(prices[i] - prices[i - 1]) for i in range(1, len(prices))]
    return sum(tr[-14:]) / 14


# ---------------- SIGNAL ----------------
def generate_signal(prices):
    ema9 = ema(prices, 9)[-1]
    ema21 = ema(prices, 21)[-1]

    rsi_val = rsi(prices)
    atr_val = atr(prices)

    price = prices[-1]
    prev = prices[-2]

    if atr_val < 0.3:
        return "NO TRADE", price

    if ema9 > ema21 and price > prev and rsi_val > 50:
        return "BUY", price

    if ema9 < ema21 and price < prev and rsi_val < 50:
        return "SELL", price

    return "NO TRADE", price


# ---------------- LOOP ----------------
async def watch_loop(context, chat_id):
    global running

    while running:
        prices = get_prices()

        if not prices:
            await asyncio.sleep(10)
            continue

        sig, price = generate_signal(prices)
        atr_val = atr(prices)

        if sig != "NO TRADE":
            sl = atr_val * 1.5
            tp = atr_val * 3

            if sig == "BUY":
                sl_price = price - sl
                tp_price = price + tp
            else:
                sl_price = price + sl
                tp_price = price - tp

            msg = f"""
📊 XAU/USD SIGNAL

📌 {sig}
💰 Entry: {price:.2f}
🛑 SL: {sl_price:.2f}
🎯 TP: {tp_price:.2f}
"""

            await context.bot.send_message(chat_id=chat_id, text=msg)

            running = False
            break

        await asyncio.sleep(20)


# ---------------- TELEGRAM ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bot ishlayapti")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    running = True

    chat_id = update.effective_chat.id

    await update.message.reply_text("📡 Signal started...")

    asyncio.create_task(watch_loop(context, chat_id))


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    running = False
    await update.message.reply_text("🛑 Stop")


# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("stop", stop))

    threading.Thread(target=run_server, daemon=True).start()

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
    if "values" not in r:
            return None

        prices = [float(i["close"]) for i in r["values"]]
        prices.reverse()

        return prices if len(prices) >= 30 else None

    except:
        return None


# ---------------- INDICATORS ----------------
def ema(prices, n):
    k = 2 / (n + 1)
    out = [prices[0]]
    for p in prices[1:]:
        out.append(p * k + out[-1] * (1 - k))
    return out


def rsi(prices, period=14):
    gains, losses = [], []

    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(prices):
    tr = [abs(prices[i] - prices[i - 1]) for i in range(1, len(prices))]
    return sum(tr[-14:]) / 14


# ---------------- SIGNAL ENGINE ----------------
def generate_signal(prices):
    ema9 = ema(prices, 9)[-1]
    ema21 = ema(prices, 21)[-1]

    rsi_val = rsi(prices)
    atr_val = atr(prices)

    price = prices[-1]
    prev = prices[-2]

    if atr_val < 0.3:
        return "NO TRADE", price

    if ema9 > ema21 and price > prev and rsi_val > 50:
        return "BUY", price

    if ema9 < ema21 and price < prev and rsi_val < 50:
        return "SELL", price

    return "NO TRADE", price


# ---------------- LOOP ----------------
async def watch_loop(context, chat_id):
    global running

    while running:
        prices = get_prices()

        if not prices:
            await asyncio.sleep(10)
            continue

        sig, price = generate_signal(prices)
        atr_val = atr(prices)

        if sig != "NO TRADE":
            sl = atr_val * 1.5
            tp = atr_val * 3

            if sig == "BUY":
                sl_price = price - sl
                tp_price = price + tp
            else:
                sl_price = price + sl
                tp_price = price - tp

            msg = f"""
📊 XAU/USD SIGNAL

📌 {sig}
💰 Entry: {price:.2f}
🛑 SL: {sl_price:.2f}
🎯 TP: {tp_price:.2f}
"""

            await context.bot.send_message(chat_id=chat_id, text=msg)

            running = False
            break

        await asyncio.sleep(20)


# ---------------- TELEGRAM ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Bot ishlayapti")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    running = True

    chat_id = update.effective_chat.id

    await update.message.reply_text("📡 Signal started...")

    asyncio.create_task(watch_loop(context, chat_id))


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    running = False
    await update.message.reply_text("🛑 Stop")


# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("stop", stop))

    # Render fix server
    threading.Thread(target=run_server, daemon=True).start()

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()# ---------------- ATR ----------------
def atr(prices):
    tr = [abs(prices[i] - prices[i - 1]) for i in range(1, len(prices))]
    return sum(tr[-14:]) / 14


# ---------------- SIGNAL ENGINE ----------------
def generate_signal(prices):
    ema9 = ema(prices, 9)[-1]
    ema21 = ema(prices, 21)[-1]

    rsi_val = rsi(prices)
    atr_val = atr(prices)

    price = prices[-1]
    prev = prices[-2]

    # ❌ bozor sust
    if atr_val < 0.3:
        return "NO TRADE", price

    bullish = price > prev
    bearish = price < prev

    # 🔥 BUY
    if ema9 > ema21 and bullish and rsi_val > 50:
        return "BUY", price

    # 🔥 SELL
    if ema9 < ema21 and bearish and rsi_val < 50:
        return "SELL", price

    return "NO TRADE", price


# ---------------- BACKGROUND LOOP ----------------
async def watch_loop(context, chat_id):
    global running

    while running:
        prices = get_prices()

        if not prices:
            await asyncio.sleep(10)
            continue

        sig, price = generate_signal(prices)

        if sig != "NO TRADE":
            atr_val = atr(prices)

            sl = atr_val * 1.5
            tp = atr_val * 3

            if sig == "BUY":
                sl_price = price - sl
                tp_price = price + tp
            else:
                sl_price = price + sl
                tp_price = price - tp

            msg = f"""
📊 XAU/USD SIGNAL

📌 Signal: {sig}

💰 Entry: {price:.2f}
🛑 SL: {sl_price:.2f}
🎯 TP: {tp_price:.2f}
"""

            await context.bot.send_message(chat_id=chat_id, text=msg)

            running = False
            break

        await asyncio.sleep(20)


# ---------------- COMMANDS ----------------
async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    running = True

    chat_id = update.effective_chat.id

    await update.message.reply_text("👀 Bot ishga tushdi... signal kutilyapti")

    asyncio.create_task(watch_loop(context, chat_id))


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global running
    running = False
    await update.message.reply_text("🛑 To‘xtatildi")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/signal - start\n/stop - stop")


# ---------------- RUN ----------------
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("signal", signal))
app.add_handler(CommandHandler("stop", stop))

app.run_polling()
import os

PORT = int(os.environ.get("PORT", 10000))

print("Bot started...")
