import os
import smtplib
import requests
from email.message import EmailMessage
from datetime import datetime, timedelta

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MODTAGER_EMAIL = os.getenv("MODTAGER_EMAIL")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

SIDSTE_TJEK_FIL = "sidste_tjek.txt"
OVERVAAG_AKTIER_FIL = "overvaag_aktier.txt"

KENDTE_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "NFLX", "NVO"]

def hent_anbefaling(ticker):
    url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={ticker}&token={FINNHUB_API_KEY}"
    r = requests.get(url)
    if r.status_code == 200 and r.json():
        data = r.json()[0]
        return {
            "symbol": ticker,
            "strongBuy": data.get("strongBuy", 0),
            "buy": data.get("buy", 0),
            "hold": data.get("hold", 0),
            "sell": data.get("sell", 0),
            "strongSell": data.get("strongSell", 0)
        }
    return None

def vurder_nyhed(tekst):
    tekst = tekst.lower()
    gode = ["stigning", "rekord", "overskud", "forbedret", "vækst", "positiv", "partner", "løft", "køb", "investering"]
    skidt = ["fald", "underskud", "problem", "nedjustering", "tab", "negativ", "bøde", "undersøgelse", "skandale"]
    score = sum(1 for ord in gode if ord in tekst) - sum(1 for ord in skidt if ord in tekst)
    return "Godt" if score > 0 else "Skidt" if score < 0 else "Neutral"

def hent_nyheder(ticker, fra_dato):
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={fra_dato}&to={datetime.today().strftime('%Y-%m-%d')}&token={FINNHUB_API_KEY}"
    r = requests.get(url)
    return r.json() if r.status_code == 200 else []

def hent_overvaagede_aktier():
    if os.path.exists(OVERVAAG_AKTIER_FIL):
        with open(OVERVAAG_AKTIER_FIL, "r") as f:
            return [linje.strip() for linje in f if linje.strip()]
    return []

def load_sidste_tjek():
    if os.path.exists(SIDSTE_TJEK_FIL):
        with open(SIDSTE_TJEK_FIL, "r") as f:
            return f.read().strip()
    return (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

def save_sidste_tjek():
    with open(SIDSTE_TJEK_FIL, "w") as f:
        f.write(datetime.today().strftime('%Y-%m-%d'))

def lav_mail_tekst():
    tekst = "📈 Dagens top-anbefalede aktier:\n\n"
    anbefalinger = []

    for ticker in KENDTE_TICKERS:
        data = hent_anbefaling(ticker)
        if data:
            data["score"] = data["strongBuy"] + data["buy"]
            anbefalinger.append(data)

    anbefalinger.sort(key=lambda x: x["score"], reverse=True)
    top5 = anbefalinger[:5]

    if not top5:
        tekst += "Ingen anbefalinger fundet i dag.\n"
    else:
        for aktie in top5:
            tekst += (
                f"{aktie['symbol']} – Strong Buy: {aktie['strongBuy']}, "
                f"Buy: {aktie['buy']}, Hold: {aktie['hold']}, Sell: {aktie['sell']}\n"
            )

    tekst += "\n📰 Nyheder om overvågede aktier:\n\n"
    fra_dato = load_sidste_tjek()
    for aktie in hent_overvaagede_aktier():
        nyheder = hent_nyheder(aktie, fra_dato)
        if nyheder:
            tekst += f"{aktie}:\n"
            for n in nyheder[:3]:
                vurdering = vurder_nyhed(n['headline'])
                tekst += f"- {n['headline']} (Vurdering: {vurdering})\n"
            tekst += "\n"
    save_sidste_tjek()
    return tekst

def send_mail(indhold):
    msg = EmailMessage()
    msg["Subject"] = "📬 Dagens aktiemail"
    msg["From"] = SMTP_USERNAME
    msg["To"] = MODTAGER_EMAIL
    msg.set_content(indhold)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    try:
        tekst = lav_mail_tekst()
        send_mail(tekst)
        print("Mail sendt.")
    except Exception as e:
        print("Fejl:", e)
