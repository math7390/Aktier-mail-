import yfinance as yf
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# --- Dine API-nøgler og mail info ---
FINNHUB_API_KEY = 'd21n6phr01qpst75rt2gd21n6phr01qpst75rt30'  # Din Finnhub nøgle
NEWSAPI_KEY = 'DIN_NEWSAPI_KEY_HER'  # Din NewsAPI nøgle
SMTP_USERNAME = 'dinmail@gmail.com'
SMTP_PASSWORD = 'dit-app-password'
MODTAGER_EMAIL = 'modtager@mail.dk'

# --- Aktier opdelt på kontinent med symbol og navn ---
AKTIER = {
    'Europa': ['NVO.CO', 'SAP.DE', 'ASML.AS', 'SIE.DE', 'AIR.PA'],
    'Amerika': ['AAPL', 'MSFT', 'TSLA', 'GOOGL', 'AMZN'],
    'Asien': ['BABA', 'TCS.NS', '005930.KS', 'INFY.NS', 'JD'],
    'Afrika': ['MTN.JO', 'NPN.JO', 'SHP.JO', 'CPI.JO', 'SBK.JO']
}

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
    if res.status_code != 200:
        return None
    data = res.json()
    if not data:
        return None
    # Tag nyeste periode (sidste i listen)
    nyeste = data[-1]
    return {
        'strongBuy': nyeste.get('strongBuy', 0),
        'buy': nyeste.get('buy', 0),
        'hold': nyeste.get('hold', 0),
        'sell': nyeste.get('sell', 0),
        'strongSell': nyeste.get('strongSell', 0)
    }

def hent_nyheder(symbol):
    # Søger på firmanavn og symbol for bedre dækning
    query = symbol
    url = f'https://newsapi.org/v2/everything?q={query}&language=en&sortBy=publishedAt&pageSize=3&apiKey={NEWSAPI_KEY}'
    res = requests.get(url)
    if res.status_code != 200:
        return []
    artikler = res.json().get('articles', [])
    nyheder = []
    for a in artikler:
        titel = a['title']
        dato = a['publishedAt'][:10]
        # Enkel sentiment - positiv, neutral eller negativ ud fra keywords (kan udbygges)
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
    # Emojis for ratings
    emojis = {
        'strongBuy': '🟢',
        'buy': '✅',
        'hold': '⚪',
        'sell': '🔻',
        'strongSell': '🔴'
    }
    rating_tekst = ''
    if ratings:
        rating_tekst = (f"📊 Anbefalinger: "
                        f"{emojis['strongBuy']} Strong Buy: {ratings['strongBuy']} | "
                        f"{emojis['buy']} Buy: {ratings['buy']} | "
                        f"{emojis['hold']} Hold: {ratings['hold']} | "
                        f"{emojis['sell']} Sell: {ratings['sell']} | "
                        f"{emojis['strongSell']} Strong Sell: {ratings['strongSell']}")
    nyheds_tekst = ""
    if nyheder:
        nyheds_tekst += "📰 Nyheder:\n"
        for n in nyheder:
            nyheds_tekst += f"• {n['sentiment']} – {n['titel']} ({n['dato']})\n"
    else:
        nyheds_tekst += "📰 Ingen relevante nyheder fundet.\n"
    return (f"🔹 {info['symbol']}: {info['kurs']} USD\n"
            f"{info['navn']} – {info['sektor']} | {info['land']}\n"
            f"📃 {info['beskrivelse']}\n"
            f"{rating_tekst}\n"
            f"{nyheds_tekst}\n")

def lav_mail_tekst():
    tekst = f"Dagens aktieanalyse – {datetime.now().strftime('%Y-%m-%d')}\n\n"
    for kontinent, symbols in AKTIER.items():
        tekst += f"🌍 {kontinent}\n\n"
        for sym in symbols:
            info = hent_aktieinfo(sym)
            ratings = hent_analyst_ratings(sym)
            nyheder = hent_nyheder(sym)
            tekst += formater_aktie_tekst(info, ratings, nyheder)
            tekst += "\n"
    return tekst

def send_mail(tekst):
    message = MIMEText(tekst, _charset='utf-8')
    message['Subject'] = 'Dagens aktieanalyse'
    message['From'] = SMTP_USERNAME
    message['To'] = MODTAGER_EMAIL

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(SMTP_USERNAME, SMTP_PASSWORD)
        smtp.sendmail(SMTP_USERNAME, MODTAGER_EMAIL, message.as_string())

if __name__ == "__main__":
    mail_tekst = lav_mail_tekst()
    print(mail_tekst)  # Til debug kan du se output i konsol
    send_mail(mail_tekst)
    print("Mail sendt.")
