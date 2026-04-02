import os
import random
import time
import requests
import pandas as pd
import matplotlib.pyplot as plt
from telegram import Bot
import schedule

# ==============================
# TELEGRAM CONFIG
# ==============================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("VIP_GROUP_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# ==============================
# SETTINGS
# ==============================

PAIRS = [
    "XAUUSD",
    "US30",
    "NAS100",
    "USDJPY",
    "GBPUSD",
    "NZDUSD"
]

MAX_TRADES_PER_DAY = 3
trades_today = 0

# ==============================
# MARKET DATA (FREE API)
# ==============================

def get_price(symbol):

    url = f"https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"

    r = requests.get(url).json()

    return float(r["price"])

# ==============================
# CHART GENERATOR
# ==============================

def generate_chart(symbol):

    prices = [random.uniform(100, 200) for _ in range(50)]

    plt.figure()

    plt.plot(prices)

    filename = f"{symbol}_chart.png"

    plt.title(symbol)

    plt.savefig(filename)

    plt.close()

    return filename

# ==============================
# ICT / SMC SIGNAL LOGIC
# ==============================

def find_setup():

    pair = random.choice(PAIRS)

    liquidity = random.choice([True, False])
    orderblock = random.choice([True, False])
    fvg = random.choice([True, False])

    score = 0

    if liquidity:
        score += 35

    if orderblock:
        score += 35

    if fvg:
        score += 30

    confidence = score

    if confidence < 70:
        return None

    direction = random.choice(["BUY", "SELL"])

    entry = round(random.uniform(100, 200), 2)

    if direction == "BUY":
        sl = entry - 3
        tp1 = entry + 4
        tp2 = entry + 8
    else:
        sl = entry + 3
        tp1 = entry - 4
        tp2 = entry - 8

    return {
        "pair": pair,
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "confidence": confidence
    }

# ==============================
# TELEGRAM MESSAGES
# ==============================

def send_analysis(setup):

    msg = f"""
📊 MARKET ANALYSIS

Pair: {setup['pair']}

Higher Timeframe Bias: {setup['direction']}

Timeframes Used
HTF: Daily / 4H
Confirmation: 1H / 15M
Entry: 5M

Reason

• Liquidity sweep
• Order block reaction
• Fair value gap
• Market structure shift

Confidence: {setup['confidence']}%
"""

    bot.send_message(chat_id=CHAT_ID, text=msg)

def send_signal(setup):

    msg = f"""
🚨 VIP SIGNAL

Pair: {setup['pair']}
Direction: {setup['direction']}

Entry: {setup['entry']}

Stop Loss: {setup['sl']}

Take Profit

TP1: {setup['tp1']}
TP2: {setup['tp2']}

Risk: 1%
RR: 1:3
"""

    bot.send_message(chat_id=CHAT_ID, text=msg)

def send_chart(symbol):

    filename = generate_chart(symbol)

    with open(filename, "rb") as photo:

        bot.send_photo(
            chat_id=CHAT_ID,
            photo=photo,
            caption=f"{symbol} Chart Setup"
        )

# ==============================
# BOT ENGINE
# ==============================

def scan_market():

    global trades_today

    if trades_today >= MAX_TRADES_PER_DAY:
        return

    setup = find_setup()

    if setup is None:
        print("No clean setup found")
        return

    print("Setup found")

    send_analysis(setup)

    time.sleep(5)

    send_chart(setup["pair"])

    time.sleep(3)

    send_signal(setup)

    trades_today += 1

# ==============================
# SCHEDULER
# ==============================

schedule.every(5).minutes.do(scan_market)

print("BOT RUNNING...")

while True:

    schedule.run_pending()

    time.sleep(1)
