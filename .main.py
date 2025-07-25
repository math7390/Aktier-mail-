import smtplib
import yfinance as yf
import requests
from datetime import datetime
import os

# Miljøvariabler
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
MODTAGER_EMAIL = os.environ.get("MODTAGER_EMAIL")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")

# Overvågede aktier
overvågede_aktier = ["AAPL", "NVO", "SHOP"]

# Hent info om aktier
def hent_aktieinfo(symbol):
    aktie = yf.Ticker(symbol)
    info = aktie.info

    try:
        kurs = round(info.get("currentPrice", 0), 2)
        navn = info.get("shortName", "Ukendt navn")
        sektor = info.get("sector", "Ukendt sektor")
        land = info.get("country", "Ukendt land")
        beskrivelse = info.get("longBusinessSummary", "Ingen beskrivelse")
        return {
            "symbol": symbol,
            "kurs": kurs,
            "navn": navn,
            "sektor": sektor,
            "land": land,
            "beskrivelse": beskrivelse
        }
    except Exception:
        return None

# Hent anbefalinger fra Finnhub
def hent_anbefalinger(symbol):
    url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={symbol}&token={FINNHUB_API_KEY}"
    try:
        res = requests.get(url)
        data = res.json()
        if isinstance(data, list) and len(data) > 0:
            seneste = data[0]
            return {
                "strongBuy": seneste.get("strongBuy", 0),
                "buy": seneste.get("buy", 0),
                "hold": seneste.get("hold", 0),
                "sell": seneste.get("sell", 0),
                "strongSell": seneste.get("strongSell", 0),
            }
    except Exception:
        pass
    return None

# Hent nyheder via NewsAPI
def hent_nyheder(symbol):
    url = f"https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWSAPI_KEY}&language=da&pageSize=5"
    try:
        res = requests.get(url)
        data = res.json()
        nyheder = []
        for artikel in data.get("articles", []):
            titel = artikel.get("title", "Ukendt titel")
            dato = artikel.get("publishedAt", "")[:10]
            sentiment = "⚪ Neutral"
            if any(word in titel.lower() for word in ["stiger", "vinder", "rekord", "løfter", "god"]):
                sentiment = "📈 Positiv"
            elif any(word in titel.lower() for word in ["falder", "skuffelse", "taber", "kritik", "dårlig"]):
                sentiment = "📉 Negativ"
            nyheder.append(f"{sentiment} – {titel} ({dato})")
        return nyheder if nyheder else ["Ingen relevante nyheder fundet."]
    except Exception:
        return ["Fejl ved hentning af nyheder."]

# Sæt hele mailen sammen
def byg_mail():
    linjer = []
    linjer.append(f"Dagens aktieanalyse – {datetime.now().strftime('%Y-%m-%d')}\n")

    linjer.append("📈 Top anbefalinger:\n")
    symbols = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "NVDA", "META", "NVO", "SHOP", "BABA"]

    for symbol in symbols:
        aktie = hent_aktieinfo(symbol)
        anbefaling = hent_anbefalinger(symbol)
        if aktie:
            linjer.append(f"{symbol}: Kurs {aktie['kurs']:.2f} USD")
            linjer.append(f"💼 {aktie['navn']} – {aktie['sektor']} | {aktie['land']}")
            if anbefaling:
                linjer.append(
                    f"📊 Anbefalinger: 🟢 Strong Buy: {anbefaling['strongBuy']} | 🟢 Buy: {anbefaling['buy']} | "
                    f"🟡 Hold: {anbefaling['hold']} | 🔴 Sell: {anbefaling['sell']} | 🔴 Strong Sell: {anbefaling['strongSell']}"
                )
            linjer.append(aktie['beskrivelse'][:300] + "...\n")
    linjer.append("\n📰 Nyheder for overvågede aktier:\n")

    for symbol in overvågede_aktier:
        aktie = hent_aktieinfo(symbol)
        linjer.append(f"{symbol} – {aktie['navn'] if aktie else symbol}")
        nyheder = hent_nyheder(symbol)
        for nyhed in nyheder:
            linjer.append(f"• {nyhed}")
        linjer.append("")

    return "\n".join(linjer)

# Send mail via Gmail SMTP
def send_mail(tekst):
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        message = f"Subject: Dagens aktieanalyse\n\n{tekst}"
        smtp.sendmail(SMTP_USERNAME, MODTAGER_EMAIL, message)

# Kør script
mail_tekst = byg_mail()
send_mail(mail_tekst)
print("Mail sendt.")
