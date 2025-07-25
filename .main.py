import os
import smtplib
from email.message import EmailMessage
import yfinance as yf
from datetime import datetime

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MODTAGER_EMAIL = os.getenv("MODTAGER_EMAIL")

POPULAERE_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "NVO", "NFLX"]
OVERVAAG_AKTIER_FIL = "overvaag_aktier.txt"

def hent_anbefalinger(ticker):
    try:
        aktie = yf.Ticker(ticker)
        info = aktie.info
        anbefaling = info.get("recommendationKey", "ukendt")
        kursmaal = info.get("targetMeanPrice", "ukendt")
        return anbefaling.capitalize(), kursmaal
    except Exception as e:
        return "Fejl", "Ukendt"

def hent_overvaagede_aktier():
    if os.path.exists(OVERVAAG_AKTIER_FIL):
        with open(OVERVAAG_AKTIER_FIL, "r") as f:
            return [linje.strip() for linje in f if linje.strip()]
    return []

def lav_mail_tekst():
    tekst = f"Dagens aktieanalyse – {datetime.today().strftime('%d-%m-%Y')}\n\n"
    tekst += "📈 Top anbefalinger:\n\n"

    for ticker in POPULAERE_TICKERS:
        anbefaling, kursmaal = hent_anbefalinger(ticker)
        tekst += f"{ticker}: {anbefaling} (Kursmål: {kursmaal})\n"

    tekst += "\n📰 Overvågede aktier:\n\n"
    overvågning = hent_overvaagede_aktier()
    if overvågning:
        for aktie in overvågning:
            anbefaling, kursmaal = hent_anbefalinger(aktie)
            tekst += f"{aktie}: {anbefaling} (Kursmål: {kursmaal})\n"
    else:
        tekst += "Ingen overvågningsaktier fundet.\n"

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
        print("✅ Mail sendt!")
    except Exception as e:
        print("Fejl:", e)
