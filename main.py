import requests
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8636924036:AAGiUBAGp5LUqHbQTPAb3-nTUoDWG0jVGYg"
API_KEY = "764b9127cff041379f20e48a309586cb"
SYMBOL = "XAU/USD"

running = False


# ---------------- SAFE PRICE ----------------
def get_prices():
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={SYMBOL}&interval=5min&outputsize=100&apikey={API_KEY}"
        r = requests.get(url, timeout=10).json()

        if "values" not in r:
            return None

        prices = [float(i["close"]) for i in r["values"]]
        prices.reverse()

        if len(prices) < 30:
            return None

        return prices

    except:
        return None


# ---------------- EMA ----------------
def ema(prices, n):
    k = 2 / (n + 1)
    out = [prices[0]]
    for p in prices[1:]:
        out.append(p * k + out[-1] * (1 - k))
    return out


# ---------------- RSI ----------------
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


# ---------------- ATR ----------------
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
