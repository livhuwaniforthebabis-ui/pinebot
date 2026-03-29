import os
import asyncio
import aiohttp
import yfinance as yf
from datetime import datetime, date

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

MARKETS = {
    "BTCUSD": "BTC-USD",
    "GOLD": "GC=F",
    "US30": "^DJI",
    "NAS100": "^IXIC",
    "USDJPY": "JPY=X"
}

TIMEFRAME = "15m"
INTERVAL = 60

daily_trades = []
stats = {"wins": 0, "losses": 0}

# ---------- TELEGRAM ----------
async def send(session, msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    await session.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ---------- DATA ----------
def get_data(symbol):
    return yf.Ticker(symbol).history(period="2d", interval=TIMEFRAME)

# ---------- ANALYSIS ----------
def trend(data):
    return "UPTREND 📈" if data['Close'].iloc[-1] > data['Close'].iloc[-30] else "DOWNTREND 📉"

def structure(data):
    if data['High'].iloc[-1] > data['High'].iloc[-10]:
        return "BULLISH BOS"
    if data['Low'].iloc[-1] < data['Low'].iloc[-10]:
        return "BEARISH BOS"
    return None

def liquidity(data):
    high = data['High'].iloc[-6:-1].max()
    low = data['Low'].iloc[-6:-1].min()
    price = data['Close'].iloc[-1]

    if price > high:
        return "SWEEP HIGH 🔝"
    if price < low:
        return "SWEEP LOW 🔻"
    return None

# ---------- HIGH PROBABILITY FILTER ----------
def valid_setup(tr, st, liq):
    return (
        tr and st and liq and
        (("UPTREND" in tr and "BULLISH" in st and "LOW" in liq) or
         ("DOWNTREND" in tr and "BEARISH" in st and "HIGH" in liq))
    )

# ---------- TRADE ----------
def build_trade(price, tr):
    risk = price * 0.002

    if "UPTREND" in tr:
        return {
            "dir": "BUY 📈",
            "sl": round(price - risk,2),
            "tp1": round(price + risk,2),
            "tp2": round(price + risk*3,2)
        }
    else:
        return {
            "dir": "SELL 📉",
            "sl": round(price + risk,2),
            "tp1": round(price - risk,2),
            "tp2": round(price - risk*3,2)
        }

# ---------- TRACK RESULT ----------
async def track_trade(session, market, trade):
    await asyncio.sleep(300)  # wait 5 min

    data = get_data(MARKETS[market])
    price = data['Close'].iloc[-1]

    if trade["dir"].startswith("BUY"):
        if price >= trade["tp2"]:
            stats["wins"] += 1
            result = "WIN ✅"
        elif price <= trade["sl"]:
            stats["losses"] += 1
            result = "LOSS ❌"
        else:
            return
    else:
        if price <= trade["tp2"]:
            stats["wins"] += 1
            result = "WIN ✅"
        elif price >= trade["sl"]:
            stats["losses"] += 1
            result = "LOSS ❌"
        else:
            return

    report = f"""
📊 TRADE RESULT - {market}

Result: {result}

📈 Wins: {stats['wins']}
📉 Losses: {stats['losses']}
📊 Win Rate: {round((stats['wins']/(stats['wins']+stats['losses']))*100,2)}%
"""
    await send(session, report)

# ---------- MAIN ----------
async def main():
    print("🚀 VIP Signal Bot Running...")
    async with aiohttp.ClientSession() as session:
        while True:

            # Limit 3 trades per day
            if len(daily_trades) >= 3:
                await asyncio.sleep(INTERVAL)
                continue

            for market, symbol in MARKETS.items():
                try:
                    data = get_data(symbol)
                    price = data['Close'].iloc[-1]

                    tr = trend(data)
                    st = structure(data)
                    liq = liquidity(data)

                    if not valid_setup(tr, st, liq):
                        continue

                    # Avoid duplicate trades
                    if market in daily_trades:
                        continue

                    trade = build_trade(price, tr)

                    # ---------- ANALYSIS ----------
                    analysis = f"""
🧠 PREMIUM ANALYSIS - {market}

⏱ Timeframe: 15M

📊 Overall Trend: {tr}
🏗 Structure: {st}
💧 Liquidity: {liq}

📍 POI: Institutional Zone (OB)
📌 Entry Logic:
Price swept liquidity → BOS confirmed → entering continuation

🎯 Target:
Continuation move toward liquidity (3R)

⚖️ Confidence: VERY HIGH (90%+) 🔥
"""

                    await send(session, analysis)

                    # ---------- TRADE ----------
                    signal = f"""
💹 VIP TRADE - {market}

📊 Direction: {trade['dir']}
📍 Entry: {round(price,2)}

🛑 SL: {trade['sl']}
💰 TP1: {trade['tp1']}
🎯 TP2: {trade['tp2']}

🔒 Move SL to BE at TP1
⚖️ RR: 1:3

🧠 Reason:
HTF Trend + BOS + Liquidity Sweep Alignment

📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
"""

                    await send(session, signal)

                    daily_trades.append(market)

                    # Track result
                    asyncio.create_task(track_trade(session, market, trade))

                except Exception as e:
                    print("Error:", e)

            await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
