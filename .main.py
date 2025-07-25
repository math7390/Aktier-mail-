import smtplib
import os
import yfinance as yf
import requests
from email.mime.text import MIMEText
from datetime import datetime

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MODTAGER_EMAIL = os.getenv("MODTAGER_EMAIL")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

def hent_beskrivelse(symbol):
    try:
        aktie = yf.Ticker(symbol)
        info = aktie.info
        navn = info.get("longName", "Ukendt navn")
        sektor = info.get("sector", "Ukendt sektor")
        land = info.get("country", "Ukendt land")
        beskrivelse = info.get("longBusinessSummary", "Ingen beskrivelse tilgængelig.")[:200]
        kurs = round(info.get("currentPrice", 0), 2)
        return f"💼 {symbol} – {navn}\n💰 Kurs: {kurs} USD\n🏢 {sektor} | {land}\n📃 {beskrivelse}\n"
    except:
        return f"{symbol}: Data kunne ikke hentes\n"

def vurder_nyhed(titel):
    titel_lower = titel.lower()
    positive = ["stiger", "rekord", "opjusterer", "godkendt", "positiv", "vinder", "køber"]
    negative = ["fald", "skuffelse", "nedjusterer", "sagsanlæg", "negative", "fyringer", "sælger"]
    if any(ord in titel_lower for ord in positive):
        return "🟢 Positiv"
    elif any(ord in titel_lower for ord in negative):
        return "🔴 Negativ"
    else:
        return "⚪ Neutral"

def hent_nyheder(symbol):
    url = f"https://newsapi.org/v2/everything?q={symbol}&sortBy=publishedAt&apiKey={NEWSAPI_KEY}&language=en"
    try:
        response = requests.get(url)
        nyheder = response.json().get("articles", [])[:3]
        resultat = ""
        if not nyheder:
            return "Ingen relevante nyheder fundet.\n"
        for nyhed in nyheder:
            titel = nyhed.get("title", "Ingen titel")
            dato = nyhed.get("publishedAt", "")[:10]
            vurdering = vurder_nyhed(titel)
            resultat += f"• {vurdering} – {titel} ({dato})\n"
        return resultat
    except:
        return "Fejl ved hentning af nyheder.\n"

def hent_overvaagede_aktier():
    try:
        with open("overvaagede_aktier.txt", "r") as f:
            return [linje.strip().upper() for linje in f if linje.strip()]
    except:
        return []

def hent_top_anbefalede():
    top_aktier = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "NVDA", "META", "NVO", "SHOP", "BABA"]
    return top_aktier

def sammensæt_mail():
    dato = datetime.now().strftime("%Y-%m-%d")
    mail = f"Dagens aktieanalyse – {dato}\n\n📈 Top anbefalinger:\n\n"

    for symbol in hent_top_anbefalede():
        mail += hent_beskrivelse(symbol)
        mail += hent_nyheder(symbol)
        mail += "\n"

    overvågede = hent_overvaagede_aktier()
    if overvågede:
        mail += "🕵️ Overvågede aktier:\n\n"
        for symbol in overvågede:
            mail += hent_beskrivelse(symbol)
            mail += hent_nyheder(symbol)
            mail += "\n"
    return mail

def send_mail(tekst):
    smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    smtp.starttls()
    smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
    message = MIMEText(tekst, "plain", "utf-8")
    message["Subject"] = "📊 Daglig Aktieanalyse"
    message["From"] = SMTP_USERNAME
    message["To"] = MODTAGER_EMAIL
    smtp.sendmail(SMTP_USERNAME, MODTAGER_EMAIL, message.as_string())
    smtp.quit()

if __name__ == "__main__":
    mail_tekst = sammensæt_mail()
    send_mail(mail_tekst)
    print("✅ Mail sendt.")
