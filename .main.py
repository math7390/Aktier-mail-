import yfinance as yf
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime

# --- KONFIGURATION ---
SMTP_USERNAME = "din_gmail@gmail.com"
SMTP_PASSWORD = "dit_app_password"
MODTAGER_EMAIL = "modtager@mail.dk"
NEWSAPI_KEY = "din_newsapi_nøgle"

# Aktier opdelt på kontinenter med land og beskrivelse
kontinent_aktier = {
    "Europa": [
        {"symbol": "NOKIA.HE", "navn": "Nokia Corporation", "sektor": "Communication Equipment", "land": "Finland", "flag": "🇫🇮", "beskrivelse": "Leverer netværksinfrastruktur og teknologiløsninger globalt."},
        # Tilføj flere her
    ],
    "Asien": [
        {"symbol": "BABA", "navn": "Alibaba Group", "sektor": "Consumer Cyclical", "land": "Hong Kong", "flag": "🇭🇰", "beskrivelse": "Driver en global e-handelsplatform og tech-infrastruktur."},
        # Flere aktier her
    ],
    "Amerika": [
        {"symbol": "AAPL", "navn": "Apple Inc.", "sektor": "Technology", "land": "United States", "flag": "🇺🇸", "beskrivelse": "Producerer smartphones, computere og software globalt."},
        # Flere aktier her
    ],
    "Afrika": [
        {"symbol": "MTN.JO", "navn": "MTN Group Limited", "sektor": "Telecommunications", "land": "South Africa", "flag": "🇿🇦", "beskrivelse": "Telekomgigant i Afrika med mobildækning i 20+ lande."},
        # Flere aktier her
    ],
}

def hent_aktiekurs(symbol):
    try:
        aktie = yf.Ticker(symbol)
        kurs = aktie.info.get("regularMarketPrice")
        return round(kurs, 2) if kurs else None
    except Exception:
        return None

def hent_nyheder(symbol):
    url = f"https://newsapi.org/v2/everything?q={symbol}&apiKey={NEWSAPI_KEY}&language=en&pageSize=3&sortBy=publishedAt"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    data = response.json()
    nyheder = []
    for artikel in data.get("articles", []):
        titel = artikel.get("title", "")
        dato = artikel.get("publishedAt", "")[:10]
        # Enkel impact vurdering via keywords (kan udbygges)
        impact = "⚪"  # neutral default
        titellower = titel.lower()
        if any(word in titellower for word in ["profit", "beat", "growth", "positive"]):
            impact = "🟢"
        elif any(word in titellower for word in ["loss", "miss", "decline", "negative", "lawsuit"]):
            impact = "🔴"
        nyheder.append({"titel": titel, "dato": dato, "impact": impact})
    return nyheder

def formater_aktieinfo(aktie):
    kurs = hent_aktiekurs(aktie["symbol"])
    kurs_str = f"{kurs} USD" if kurs else "Kurs ikke tilgængelig"
    tekst = (f"{aktie['flag']} 🔹 {aktie['symbol']}: {kurs_str}\n"
             f"{aktie['navn']} – {aktie['sektor']} | {aktie['land']}\n"
             f"📃 {aktie['beskrivelse']}\n")
    return tekst

def formater_nyheder(nyheder):
    if not nyheder:
        return "Ingen relevante nyheder fundet.\n"
    tekst = ""
    for nyhed in nyheder:
        tekst += f"• {nyhed['impact']} {nyhed['titel']} ({nyhed['dato']})\n"
    return tekst

def lav_mailtekst():
    tekst = f"Dagens aktieanalyse – {datetime.date.today()}\n\n"
    for kontinent, aktier in kontinent_aktier.items():
        tekst += f"🌍 {kontinent}\n\n"
        for aktie in aktier:
            tekst += formater_aktieinfo(aktie) + "\n"
        tekst += "\n"
    tekst += "📰 Nyheder for overvågede aktier:\n\n"
    for kontinent, aktier in kontinent_aktier.items():
        for aktie in aktier:
            tekst += f"🔍 {aktie['symbol']} – {aktie['navn']}\n"
            nyheder = hent_nyheder(aktie["symbol"])
            tekst += formater_nyheder(nyheder) + "\n"
    return tekst

def send_mail(tekst):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USERNAME
    msg["To"] = MODTAGER_EMAIL
    msg["Subject"] = f"Dagens aktieanalyse - {datetime.date.today()}"
    msg.attach(MIMEText(tekst, "plain", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.sendmail(SMTP_USERNAME, MODTAGER_EMAIL, msg.as_string())

if __name__ == "__main__":
    mail_tekst = lav_mailtekst()
    print(mail_tekst)  # For debug, kan fjernes i produktion
    send_mail(mail_tekst)
