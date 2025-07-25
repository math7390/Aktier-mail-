import os
import smtplib
from email.message import EmailMessage
import requests
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp-relay.brevo.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
MODTAGER_EMAIL = os.getenv("MODTAGER_EMAIL")

# Dine egne aktier (kan ændres frit)
mine_aktier = ["AAPL", "TSLA", "NOVO-B.CO"]

def hent_anbefalinger(ticker):
    url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={ticker}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            anbefaling = data[0]
            return f"{ticker}: 📈 {anbefaling['strongBuy']} Strong Buy / 🟢 {anbefaling['buy']} Buy / ⚪ {anbefaling['hold']} Hold / 🔴 {anbefaling['sell']} Sell / 🔻 {anbefaling['strongSell']} Strong Sell"
    return f"{ticker}: Ingen data"

def lav_daglig_mail():
    besked = "📊 Dagens analytikeranbefalinger:\n\n"
    for aktie in mine_aktier:
        besked += hent_anbefalinger(aktie) + "\n"
    return besked

def send_mail(indhold):
    msg = EmailMessage()
    msg["Subject"] = "📬 Dagens aktieanbefalinger"
    msg["From"] = SMTP_USERNAME
    msg["To"] = MODTAGER_EMAIL
    msg.set_content(indhold)

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(msg)

if __name__ == "__main__":
    mail_tekst = lav_daglig_mail()
    send_mail(mail_tekst)
