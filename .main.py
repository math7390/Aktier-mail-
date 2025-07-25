import os
import smtplib
from email.message import EmailMessage
import requests
from datetime import datetime, timedelta

# Miljøvariabler (skal sættes i Render)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MODTAGER_EMAIL = os.getenv("MODTAGER_EMAIL")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# Liste af aktier til anbefalinger
mine_aktier = ["AAPL", "TSLA", "NVO"]

# Liste af aktier til overvågning af nyheder
overvaag_aktier = ["AAPL", "NVO"]

# Gem tid for sidste tjek i en fil (for simpel persistens)
SIDSTE_TJEK_FIL = "sidste_tjek.txt"

def hent_anbefalinger(ticker):
    url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={ticker}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return (f"{ticker} anbefalinger:\n"
                f"  Strong Buy: {data['strongBuy']}\n"
                f"  Buy: {data['buy']}\n"
                f"  Hold: {data['hold']}\n"
                f"  Sell: {data['sell']}\n"
                f"  Strong Sell: {data['strongSell']}\n")
    else:
        return f"{ticker}: Ingen anbefalinger tilgængelige\n"

def hent_nyheder(ticker, fra_dato):
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={fra_dato}&to={datetime.today().strftime('%Y-%m-%d')}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return []

def vurder_nyhed(tekst):
    tekst = tekst.lower()
    gode_ord = ["stigning", "rekord", "overskud", "forbedret", "positiv", "vækst", "stærk"]
    skidt_ord = ["fald", "underskud", "problem", "nedjustering", "tab", "svag", "negativ"]
    score = 0
    for ord in gode_ord:
        if ord in tekst:
            score += 1
    for ord in skidt_ord:
        if ord in tekst:
            score -= 1
    if score > 0:
        return "Godt"
    elif score < 0:
        return "Skidt"
    else:
        return "Neutral"

def load_sidste_tjek():
    if os.path.exists(SIDSTE_TJEK_FIL):
        with open(SIDSTE_TJEK_FIL, "r") as f:
            return f.read().strip()
    else:
        return (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d')

def save_sidste_tjek():
    with open(SIDSTE_TJEK_FIL, "w") as f:
        f.write(datetime.today().strftime('%Y-%m-%d'))

def lav_mail_tekst():
    tekst = "📊 Dagens analytikeranbefalinger:\n\n"
    for aktie in mine_aktier:
        tekst += hent_anbefalinger(aktie) + "\n"

    tekst += "\n📰 Nye nyheder på overvågede aktier:\n\n"
    sidste_tjek = load_sidste_tjek()

    for aktie in overvaag_aktier:
        nyheder = hent_nyheder(aktie, sidste_tjek)
        if nyheder:
            tekst += f"{aktie}:\n"
            for nyhed in nyheder:
                headline = nyhed.get("headline", "")
                kort = vurder_nyhed(headline)
                tekst += f"- {headline} (Vurdering: {kort})\n"
            tekst += "\n"
    save_sidste_tjek()
    return tekst

def send_mail(indhold):
    msg = EmailMessage()
    msg["Subject"] = "📬 Dagens aktieopdateringer"
    msg["From"] = SMTP_USERNAME
    msg["To"] = MODTAGER_EMAIL
    msg.set_content(indhold)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    try:
        mail_tekst = lav_mail_tekst()
        send_mail(mail_tekst)
        print("Mail sendt succesfuldt!")
    except Exception as e:
        print("🚨 FEJL:", e)
