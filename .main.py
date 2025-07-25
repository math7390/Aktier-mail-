import yfinance as yf
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import os

# === ENVIRONMENT VARIABLER ===
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
MODTAGER_EMAIL = os.environ.get("MODTAGER_EMAIL")
NEWS_API_KEY = os.environ.get("NEWSAPI_KEY")

# === AKTIER TIL OVERVÅGNING ===
overvågede_aktier = ["AAPL", "SHOP", "NVO"]

# === FUNKTION: HENT BESKRIVELSE, KURS OG SEKTOR ===
def hent_aktiedata(tickers):
    data = []
    for symbol in tickers:
        aktie = yf.Ticker(symbol)
        info = aktie.info

        navn = info.get("shortName", "Ukendt")
        sektor = info.get("sector", "Ukendt")
        land = info.get("country", "Ukendt")
        beskrivelse = info.get("longBusinessSummary", "Ingen beskrivelse.")
        pris = round(info.get("regularMarketPrice", 0), 2)

        data.append({
            "symbol": symbol,
            "navn": navn,
            "sektor": sektor,
            "land": land,
            "pris": pris,
            "beskrivelse": beskrivelse
        })
    return data

# === FUNKTION: HENT NYHEDER ===
def hent_nyheder(symbol):
    url = f"https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWS_API_KEY}&language=en"
    response = requests.get(url)
    nyheder = []
    if response.status_code == 200:
        data = response.json()
        for artikel in data.get("articles", [])[:3]:
            titel = artikel["title"]
            dato = artikel["publishedAt"][:10]
            vurdering = "⚪ Neutral"
            if any(word in titel.lower() for word in ["falls", "drops", "plunge", "lawsuit", "cut"]):
                vurdering = "🔴 Negativ"
            elif any(word in titel.lower() for word in ["rises", "beats", "record", "growth"]):
                vurdering = "🟢 Positiv"
            nyheder.append(f"{vurdering} – {titel} ({dato})")
    return nyheder if nyheder else ["Ingen relevante nyheder fundet."]

# === FUNKTION: LAV MAILINDHOLD ===
def lav_mail(aktier, overvågede):
    linjer = [f"Dagens aktieanalyse – {datetime.date.today()}\n"]

    linjer.append("📈 Top anbefalinger:\n")
    for aktie in aktier:
        linjer.append(f"🔹 {aktie['symbol']}: {aktie['pris']:.2f} USD")
        linjer.append(f"{aktie['navn']} – {aktie['sektor']} | {aktie['land']}")
        linjer.append(f"{aktie['beskrivelse'][:200]}...\n")

    linjer.append("📰 Nyheder for overvågede aktier:\n")
    for symbol in overvågede:
        navn = yf.Ticker(symbol).info.get("shortName", symbol)
        linjer.append(f"\n🔍 {symbol} – {navn}")
        nyheder = hent_nyheder(symbol)
        for nyhed in nyheder:
            linjer.append(f"• {nyhed}")
        linjer.append("")

    return "\n".join(linjer)

# === FUNKTION: SEND MAIL ===
def send_mail(indhold):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USERNAME
    msg["To"] = MODTAGER_EMAIL
    msg["Subject"] = "📊 Daglig aktieanalyse og nyheder"

    msg.attach(MIMEText(indhold, "plain", "utf-8"))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(msg)

# === HOVEDPROGRAM ===
top_aktier = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "NVDA", "META", "NVO", "SHOP", "BABA"]
aktiedata = hent_aktiedata(top_aktier)
mail_tekst = lav_mail(aktiedata, overvågede_aktier)
send_mail(mail_tekst)
print("✅ Mail sendt.")
