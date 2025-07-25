import os
import smtplib
from email.mime.text import MIMEText
import requests
import datetime
import yfinance as yf

# ENV variables
SMTP_USERNAME = os.environ.get("SMTP_USERNAME")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
MODTAGER_EMAIL = os.environ.get("MODTAGER_EMAIL")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")

# Overvågede aktier (du kan ændre disse)
overvågede_aktier = ["SHOP", "NVO", "AAPL"]

# Hent top-anbefalinger
def hent_anbefalinger():
    populære = ["AAPL", "MSFT", "TSLA", "GOOGL", "AMZN", "NVDA", "META", "NVO", "SHOP", "BABA"]
    anbefalinger = []

    for symbol in populære:
        url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={symbol}&token={FINNHUB_API_KEY}"
        res = requests.get(url)
        if res.status_code == 200 and res.json():
            seneste = res.json()[0]
            score = seneste["strongBuy"] + seneste["buy"] - seneste["sell"] - seneste["strongSell"]
            if score > 0:
                anbefalinger.append((symbol, seneste, score))

    anbefalinger.sort(key=lambda x: x[2], reverse=True)
    return anbefalinger[:10]

# Hent firmainfo
def hent_firmainfo(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    return {
        "name": info.get("longName", ""),
        "description": info.get("longBusinessSummary", ""),
        "sector": info.get("sector", ""),
        "country": info.get("country", "")
    }

# Hent nyheder og vurder dem
def hent_nyheder(symbol):
    url = f"https://finnhub.io/api/v1/company-news?symbol={symbol}&from={datetime.date.today() - datetime.timedelta(days=3)}&to={datetime.date.today()}&token={FINNHUB_API_KEY}"
    res = requests.get(url)
    nyheder = []
    if res.status_code == 200 and res.json():
        for n in res.json()[:3]:
            vurdering = vurder_sentiment(n["headline"])
            nyheder.append({
                "headline": n["headline"],
                "summary": n.get("summary", ""),
                "datetime": datetime.datetime.fromtimestamp(n["datetime"]).strftime('%Y-%m-%d'),
                "url": n["url"],
                "impact": vurdering
            })
    return nyheder

# Vurder sentiment (simpel)
def vurder_sentiment(text):
    text = text.lower()
    positive = ["stiger", "vækst", "rekord", "højere", "overskud", "positiv", "bedre end ventet"]
    negative = ["falder", "nedgang", "skuffelse", "underskud", "sag", "negativ", "værre end ventet"]
    if any(p in text for p in positive):
        return "🔵 Positiv"
    elif any(n in text for n in negative):
        return "🔴 Negativ"
    return "⚪ Neutral"

# Generér mailtekst
def generer_mail():
    tekst = f"Dagens aktieanalyse – {datetime.date.today()}\n\n"

    tekst += "📈 Top anbefalinger:\n\n"
    for symbol, data, _ in hent_anbefalinger():
        info = hent_firmainfo(symbol)
        anbefaling = "✅ Buy" if data["buy"] + data["strongBuy"] > data["sell"] + data["strongSell"] else "⚠️ Hold"
        kursmål = f"{data.get('targetMeanPrice', 'ukendt')} USD"
        tekst += f"{symbol}: {anbefaling} (Kursmål: {kursmål})\n"
        tekst += f"{info['name']} – {info['sector']} | {info['country']}\n"
        tekst += f"Beskrivelse: {info['description'][:200]}...\n\n"

    tekst += "📰 Nyheder for overvågede aktier:\n\n"
    for symbol in overvågede_aktier:
        info = hent_firmainfo(symbol)
        tekst += f"{symbol} – {info['name']}\n"
        nyheder = hent_nyheder(symbol)
        if not nyheder:
            tekst += "Ingen relevante nyheder de seneste dage.\n\n"
            continue
        for n in nyheder:
            tekst += f"- {n['impact']} – {n['headline']} ({n['datetime']})\n"
            tekst += f"  Kort: {n['summary'][:150]}...\n"
            tekst += f"  Læs mere: {n['url']}\n"
        tekst += "\n"

    return tekst

# Send mail
def send_mail(indhold):
    msg = MIMEText(indhold, "plain", "utf-8")
    msg["Subject"] = f"Dagens aktieanalyse – {datetime.date.today()}"
    msg["From"] = SMTP_USERNAME
    msg["To"] = MODTAGER_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.sendmail(SMTP_USERNAME, MODTAGER_EMAIL, msg.as_string())

# Kør scriptet
if __name__ == "__main__":
    mail_tekst = generer_mail()
    send_mail(mail_tekst)
    print("📬 Mail sendt.")
