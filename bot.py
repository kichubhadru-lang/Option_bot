import yfinance as yf
import requests
from datetime import datetime

token = "8843261751:AAH1vdYGkEbD755mVXdIoO72658fE6FliFM"
chat_id = "8682661998"

def get_nifty_data():
    hist = yf.Ticker("^NSEI").history(period="30d")
    price = hist["Close"].iloc[-1]
    ema20 = hist["Close"].ewm(span=20).mean().iloc[-1]
    ema50 = hist["Close"].ewm(span=50).mean().iloc[-1]
    rsi_change = hist["Close"].diff()
    gain = rsi_change.clip(lower=0).rolling(14).mean().iloc[-1]
    loss = (-rsi_change.clip(upper=0)).rolling(14).mean().iloc[-1]
    rsi = 100-(100/(1+gain/loss)) if loss!=0 else 100
    return price, ema20, ema50, rsi

def get_vix():
    hist = yf.Ticker("^INDIAVIX").history(period="5d")
    return hist["Close"].iloc[-1]

def get_strike(price, direction):
    strike = round(price/50)*50
    if direction == "CALL":
        return strike+50
    else:
        return strike-50

base = "https://api.telegram.org/bot"+token+"/sendMessage"

try:
    price, ema20, ema50, rsi = get_nifty_data()
    vix = get_vix()
    today = datetime.now().weekday()
    trend_bull = ema20 > ema50
    trend_bear = ema20 < ema50
    vix_safe = vix < 18
    rsi_bull = 40 < rsi < 65
    rsi_bear = 35 < rsi < 60
    score_bull = 0
    score_bear = 0
    if trend_bull: score_bull+=1
    if rsi_bull: score_bull+=1
    if vix_safe: score_bull+=1
    if today < 4: score_bull+=1
    if trend_bear: score_bear+=1
    if rsi_bear: score_bear+=1
    if vix_safe: score_bear+=1
    if today < 4: score_bear+=1
    strike_ce = get_strike(price, "CALL")
    strike_pe = get_strike(price, "PUT")
    if score_bull >= 3:
        msg = ("NIFTY OPTIONS SIGNAL\n====================\nNIFTY SPOT: "+str(round(price,0))+"\nTrend: BULLISH\nVIX: "+str(round(vix,1))+" ("+("Safe" if vix_safe else "High Risk")+")\nRSI: "+str(round(rsi,1))+"\nDay: "+("Good" if today<4 else "Risky")+"\n\nACTION: BUY "+str(strike_ce)+" CE\nExpiry: Current Week\n\nSL: 30% of premium\nTP1: 30% profit\nTP2: 60% profit\nTP3: 100% profit\n\nConfidence: "+("HIGH" if score_bull==4 else "MEDIUM"))
        requests.get(base, params={"chat_id":chat_id,"text":msg})
    elif score_bear >= 3:
        msg = ("NIFTY OPTIONS SIGNAL\n====================\nNIFTY SPOT: "+str(round(price,0))+"\nTrend: BEARISH\nVIX: "+str(round(vix,1))+" ("+("Safe" if vix_safe else "High Risk")+")\nRSI: "+str(round(rsi,1))+"\nDay: "+("Good" if today<4 else "Risky")+"\n\nACTION: BUY "+str(strike_pe)+" PE\nExpiry: Current Week\n\nSL: 30% of premium\nTP1: 30% profit\nTP2: 60% profit\nTP3: 100% profit\n\nConfidence: "+("HIGH" if score_bear==4 else "MEDIUM"))
        requests.get(base, params={"chat_id":chat_id,"text":msg})
    else:
        requests.get(base, params={"chat_id":chat_id,"text":"No clear options signal now. Market unclear - stay out!"})
except Exception as e:
    requests.get(base, params={"chat_id":chat_id,"text":"Bot error: "+str(e)})
