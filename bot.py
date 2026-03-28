import os
import asyncio
import aiohttp
import yfinance as yf
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Set TELEGRAM_TOKEN and CHAT_ID as environment variables.")

MARKETS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "SP500": "SPY",
    "DAX": "^GDAXI",
    "NASDAQ": "^IXIC",
    "GOLD": "GC=F",
    "OIL": "CL=F",
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "BNB": "BNB-USD"
}

previous_prices = {m: None for m in MARKETS}
previous_signals = {m: None for m in MARKETS}

INTERVAL = 60  # seconds

async def send_telegram(session, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        async with session.post(url, data={"chat_id": CHAT_ID, "text": message}) as resp:
            await resp.text()
    except Exception as e:
        print("Telegram error:", e)

def generate_signal(current, previous, market):
    if previous is None:
        return "⚪ HOLD"
    if current > previous * 1.001:  # small breakout threshold
        return "📈 BUY"
    elif current < previous * 0.999:
        return "📉 SELL"
    return "⚪ HOLD"

async def fetch_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1d", interval="1m")
        if not data.empty:
            return float(data['Close'].iloc[-1])
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
    return None

async def main():
    print("🚀 Multi-Market Signal Bot started...")
    async with aiohttp.ClientSession() as session:
        while True:
            for market, symbol in MARKETS.items():
                price = await fetch_price(symbol)
                if price is None:
                    continue

                signal = generate_signal(price, previous_prices[market], market)
                if signal != previous_signals[market]:
                    message = f"{market}\nPrice: {price:.4f}\nSignal: {signal}\nTime: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
                    await send_telegram(session, message)
                    previous_signals[market] = signal
                    print(f"Sent {market}: {signal}")

                previous_prices[market] = price
            await asyncio.sleep(INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
