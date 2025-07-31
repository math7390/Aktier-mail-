import yfinance as yf
import requests
from datetime import datetime
from mailjet_rest import Client

import os

# === Miljøvariabler ===
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
MJ_API_KEY = os.getenv("MJ_API_KEY")
MJ_API_SECRET = os.getenv("MJ_API_SECRET")
MODTAGER_EMAIL = os.getenv("MODTAGER_EMAIL")
AFSENDER_EMAIL = os.getenv("AFSENDER_EMAIL")

# === Aktier opdelt på kontinent ===
AKTIER = {
    'Europa': ['NVO.CO', 'SAP.DE', 'ASML.AS', 'SIE.DE', 'AIR.PA'],
    'Amerika': ['AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN'],
    'Asien': ['BABA', 'TCS.NS', '005930.KS', 'INFY.NS', 'JD']
}

# === Overvågede aktier (vises i separat sektion) ===
OVERVÅGNING = ['AAPL', 'SHOP', 'NVO']

def hent_aktieinfo(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    kurs = round(info.get('regularMarketPrice', 0), 2)
    sektor = info.get('sector', 'Ukendt')
    land = info.get('country', 'Ukendt')
    navn = info.get('shortName') or info.get('longName') or symbol
    beskrivelse = info.get('longBusinessSummary', '')[:200].strip() + '...'
    return {'symbol': symbol, 'kurs': kurs, 'sektor': sektor, 'land': land, 'navn': navn, 'beskrivelse': beskrivelse}

def hent_analyst_ratings(symbol):
    url = f'https://finnhub.io/api/v1/stock/recommendation?symbol={symbol}&token={FINNHUB_API_KEY}'
    res = requests.get(url)
    if res.status_code != 200 or not res.json():
        return None
    nyeste = res.json()[-1]
    return {
        'strongBuy': nyeste.get('strongBuy', 0),
        'buy': nyeste.get('buy', 0),
        'hold': nyeste.get('hold', 0),
        'sell': nyeste.get('sell', 0),
        'strongSell': nyeste.get('strongSell', 0)
    }

def hent_nyheder(symbol):
    url = f'https://newsapi.org/v2/everything?q={symbol}&language=en&sortBy=publishedAt&pageSize=3&apiKey={NEWSAPI_KEY}'
    res = requests.get(url)
    if res.status_code != 200:
        return []
    artikler = res.json().get('articles', [])
    nyheder = []
    for a in artikler:
        titel = a['title']
        dato = a['publishedAt'][:10]
        titel_lower = titel.lower()
        if any(w in titel_lower for w in ['beat', 'rise', 'gain', 'growth', 'positive', 'record']):
            sentiment = '🟢 Positiv'
        elif any(w in titel_lower for w in ['drop', 'fall', 'loss', 'negative', 'decline', 'weak']):
            sentiment = '🔴 Negativ'
        else:
            sentiment = '⚪ Neutral'
        nyheder.append({'titel': titel, 'dato': dato, 'sentiment': sentiment})
    return nyheder

def formater_aktie_tekst(info, ratings, nyheder):
    emojis = {
        'strongBuy': '🟢',
        'buy': '✅',
        'hold': '⚪',
        'sell': '🔻',
        'strongSell': '🔴'
    }
    rating_tekst = ""
    if ratings:
        rating_tekst = (f"📊 Anbefalinger: {emojis['strongBuy']} {ratings['strongBuy']} | "
                        f"{emojis['buy']} {ratings['buy']} | {emojis['hold']} {ratings['hold']} | "
                        f"{emojis['sell']} {ratings['sell']} | {emojis['strongSell']} {ratings['strongSell']}")
    nyheds_tekst = ""
    if nyheder:
        nyheds_tekst += "📰 Nyheder:\n"
        for n in nyheder:
            nyheds_tekst += f"• {n['sentiment']} – {n['titel']} ({n['dato']})\n"
    else:
        nyheds_tekst = "📰 Ingen relevante nyheder fundet.\n"

    return (f"🔹 {info['symbol']}: {info['kurs']} USD\n"
            f"{info['navn']} – {info['sektor']} | {info['land']}\n"
            f"📃 {info['beskrivelse']}\n"
            f"{rating_tekst}\n"
            f"{nyheds_tekst}\n")

def lav_mail_tekst():
    tekst = f"Dagens aktieanalyse – {datetime.now().strftime('%Y-%m-%d')}\n\n"

    for kontinent, symbols in AKTIER.items():
        tekst += f"🌍 {kontinent}\n\n"
        for symbol in symbols:
            info = hent_aktieinfo(symbol)
            ratings = hent_analyst_ratings(symbol)
            nyheder = hent_nyheder(symbol)
            tekst += formater_aktie_tekst(info, ratings, nyheder)
            tekst += "\n"

    tekst += "🔍 Overvågede aktier:\n\n"
    for symbol in OVERVÅGNING:
        info = hent_aktieinfo(symbol)
        ratings = hent_analyst_ratings(symbol)
        nyheder = hent_nyheder(symbol)
        tekst += formater_aktie_tekst(info, ratings, nyheder)
        tekst += "\n"

    return tekst

def send_mail(tekst):
    mailjet = Client(auth=(MJ_API_KEY, MJ_API_SECRET), version='v3.1')
    data = {
        'Messages': [
            {
                "From": {
                    "Email": AFSENDER_EMAIL,
                    "Name": "AktieBot"
                },
                "To": [
                    {
                        "Email": MODTAGER_EMAIL,
                        "Name": "Modtager"
                    }
                ],
                "Subject": "📈 Dagens aktieanalyse",
                "TextPart": tekst
            }
        ]
    }
    result = mailjet.send.create(data=data)
    print(result.status_code)
    print(result.json())

if __name__ == "__main__":
    mail_tekst = lav_mail_tekst()
    send_mail(mail_tekst)
