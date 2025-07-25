import os
import smtplib
from email.message import EmailMessage
import requests

# Hent miljøvariabler fra Render
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")      # Din Gmail-adresse
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")      # Dit Gmail app-password
MODTAGER_EMAIL = os.getenv("MODTAGER_EMAIL")    # Modtagerens e-mail
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")  # Din Finnhub API-nøgle

# Liste over aktier, du vil følge
mine_aktier = ["AAPL", "TSLA", "NOVO-B.CO"]

def hent_anbefalinger(ticker):
    url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={ticker}&token={FINNHUB_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            anbefaling = data[0]
            return (f"{ticker}: 📈 Strong Buy: {anbefaling['strongBuy']} | Buy: {anbefaling['buy']} | "
                    f"Hold: {anbefaling['hold']} | Sell: {anbefaling['sell']} | Strong Sell: {anbefaling['strongSell']}")
    return f"{ticker}: Ingen anbefalinger tilgængelige"

def lav_daglig_mail():
    tekst = "📊 Dagens analytikeranbefalinger:\n\n"
    for aktie in mine_aktier:
        tekst += hent_anbefalinger(aktie) + "\n"
    return tekst

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
    try:
        mail_tekst = lav_daglig_mail()
        send_mail(mail_tekst)
        print("Mail sendt succesfuldt!")
    except Exception as e:
        print("🚨 FEJL:", e)
