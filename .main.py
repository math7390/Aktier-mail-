import os
import smtplib
import yfinance as yf
import datetime
import requests
from email.mime.text import MIMEText

# Miljøvariabler
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
MODTAGER_EMAIL = os.environ.get("MODTAGER_EMAIL")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")

# Aktielister
populaere_aktier = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "NVDA", "META", "NVO", "SHOP", "BABA"]
overvaagede_aktier = ["AAPL", "SHOP", "NVO"]

def vurder_sentiment(text):
    text = text.lower()
    positive = ["stiger", "rekord", "højere", "positiv", "bedre", "godkendt", "vækst", "stærk"]
    negative = ["falder", "nedgang", "negativ", "sag", "værre", "usikkerhed", "fejl", "svag"]
    if any(p in text for p in positive):
        return "📈 Positiv"
    elif any(n in text for n in negative):
        return "📉 Negativ"
    else:
        return "⚪ Neutral"

def hent_aktie_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        kurs = ticker.fast_info.get("lastPrice", "Ukendt")
        navn = info.get("longName", symbol)
        sektor = info.get("sector", "Ukendt")
        land = info.get("country", "Ukendt")
        beskrivelse = info.get("longBusinessSummary", "Ingen beskrivelse tilgængelig").strip()
        if len(beskrivelse) > 200:
            beskrivelse = beskrivelse[:197] + "..."
        return {
            "kurs": kurs,
            "navn": navn,
            "sektor": sektor,
            "land": land,
            "beskrivelse": beskrivelse
        }
    except:
        return {
            "kurs": "Ukendt",
            "navn": symbol,
            "sektor": "Ukendt",
            "land": "Ukendt",
            "beskrivelse": "Ingen info tilgængelig."
        }

def hent_nyheder_newsapi(symbol):
    try:
        url = f"https://newsapi.org/v2/everything?q={symbol}&language=da&sortBy=publishedAt&pageSize=3&apiKey={NEWSAPI_KEY}"
        response = requests.get(url)
        data = response.json()
        nyheder = []
        for artikel in data.get("articles", []):
            titel = artikel.get("title", "Ingen titel")
            dato = artikel.get("publishedAt", "")[:10]
            sentiment = vurder_sentiment(titel)
            nyheder.append(f"{sentiment} – {titel} ({dato})")
        return nyheder
    except:
        return []

def generer_mail():
    tekst = f"Dagens aktieanalyse – {datetime.date.today()}\n\n"
    tekst += "📈 Top anbefalinger:\n\n"

    for symbol in populaere_aktier:
        info = hent_aktie_info(symbol)
        tekst += f"{symbol}: Kurs {info['kurs']} USD\n"
        tekst += f"{info['navn']} – {info['sektor']} | {info['land']}\n"
        tekst += f"{info['beskrivelse']}\n\n"

    tekst += "\n📰 Nyheder for overvågede aktier:\n\n"
    for symbol in overvaagede_aktier:
        info = hent_aktie_info(symbol)
        tekst += f"{symbol} – {info['navn']}\n"
        nyheder = hent_nyheder_newsapi(symbol)
        if not nyheder:
            tekst += "Ingen relevante nyheder fundet.\n\n"
        else:
            for n in nyheder:
                tekst += f"{n}\n"
            tekst += "\n"

    return tekst

def send_mail(indhold):
    msg = MIMEText(indhold, "plain", "utf-8")
    msg["Subject"] = f"Dagens aktieanalyse – {datetime.date.today()}"
    msg["From"] = SMTP_USERNAME
    msg["To"] = MODTAGER_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.sendmail(SMTP_USERNAME, MODTAGER_EMAIL, msg.as_string())

if __name__ == "__main__":
    mail_tekst = generer_mail()
    send_mail(mail_tekst)
    print("📬 Mail sendt.")
