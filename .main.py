import os
import smtplib
import yfinance as yf
import requests
from datetime import datetime
from email.message import EmailMessage

# Miljøvariabler i Render
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MODTAGER_EMAIL = os.getenv("MODTAGER_EMAIL")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Liste over aktier du vil overvåge
overvagede_aktier = ["AAPL", "MSFT", "TSLA", "NVO", "SHOP"]

def hent_nyheder(symbol):
    url = (
        f"https://newsapi.org/v2/everything?"
        f"q={symbol}&"
        f"language=en&"
        f"sortBy=publishedAt&"
        f"apiKey={NEWSAPI_KEY}"
    )
    resp = requests.get(url)
    data = resp.json()

    nyheder = []
    if data.get("status") != "ok":
        return nyheder

    for artikel in data.get("articles", [])[:3]:
        titel = artikel["title"]
        dato = artikel["publishedAt"][:10]
        # Simpel sentiment-analyse på titel
        title_lower = titel.lower()
        if any(w in title_lower for w in ["rise", "gain", "beat", "profit", "upgrade", "growth"]):
            sentiment = "🟢 Positiv"
        elif any(w in title_lower for w in ["fall", "drop", "loss", "downgrade", "decline", "lawsuit"]):
            sentiment = "🔴 Negativ"
        else:
            sentiment = "⚪ Neutral"
        nyheder.append(f"• {sentiment} – {titel} ({dato})")
    return nyheder

def hent_kurs_aendring_pct(symbol):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="2d")
    if len(hist) < 2:
        return 0
    close_yesterday = hist['Close'][-2]
    close_today = hist['Close'][-1]
    return round((close_today - close_yesterday) / close_yesterday * 100, 2)

def beregn_anbefaling(pos, neu, neg, kurs_ændring_pct):
    score = 0
    score += pos * 2
    score += neu * 0
    score -= neg * 2
    score += kurs_ændring_pct * 5  # Vægt kursændring højere
    
    if score > 8:
        return "🟢 Strong Buy"
    elif score > 4:
        return "✅ Buy"
    elif score > -2:
        return "⚪ Hold"
    elif score > -6:
        return "🔻 Sell"
    else:
        return "🔴 Strong Sell"

def lav_mail():
    tekst = f"Dagens aktieanalyse – {datetime.now().strftime('%Y-%m-%d')}\n\n"
    tekst += "📈 Overvågede aktier:\n\n"

    for symbol in overvagede_aktier:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        navn = info.get("shortName", "Ukendt navn")
        kurs = round(info.get("currentPrice", 0), 2)
        sektor = info.get("sector", "Ukendt sektor")
        land = info.get("country", "Ukendt land")
        beskrivelse = info.get("longBusinessSummary", "")
        if beskrivelse:
            beskrivelse = beskrivelse[:200].strip() + "..."
        else:
            beskrivelse = "Beskrivelse ikke tilgængelig."

        kurs_ændring_pct = hent_kurs_aendring_pct(symbol)
        nyheder = hent_nyheder(symbol)
        pos = sum("🟢" in n for n in nyheder)
        neu = sum("⚪" in n for n in nyheder)
        neg = sum("🔴" in n for n in nyheder)
        anbefaling = beregn_anbefaling(pos, neu, neg, kurs_ændring_pct)

        tekst += (
            f"🔹 {symbol}: {kurs} USD\n"
            f"{navn} – {sektor} | {land}\n"
            f"📃 {beskrivelse}\n"
            f"📊 Kursændring (1 dag): {kurs_ændring_pct}%\n"
            f"📈 Anbefaling: {anbefaling}\n\n"
        )

    tekst += "📰 Nyheder for overvågede aktier:\n\n"
    for symbol in overvagede_aktier:
        navn = yf.Ticker(symbol).info.get("shortName", symbol)
        tekst += f"🔍 {symbol} – {navn}\n"
        nyheder = hent_nyheder(symbol)
        if nyheder:
            for nyhed in nyheder:
                tekst += nyhed + "\n"
        else:
            tekst += "Ingen relevante nyheder fundet.\n"
        tekst += "\n"

    return tekst

def send_mail(tekst):
    message = EmailMessage()
    message["From"] = SMTP_USERNAME
    message["To"] = MODTAGER_EMAIL
    message["Subject"] = f"Dagens Aktieanalyse – {datetime.now().strftime('%Y-%m-%d')}"
    message.set_content(tekst)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.send_message(message)

if __name__ == "__main__":
    mail_tekst = lav_mail()
    send_mail(mail_tekst)
    print("Mail sendt.")
