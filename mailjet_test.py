from mailjet_rest import Client
import os

# Hent dine miljøvariabler
api_key = os.getenv("MJ_APIKEY_PUBLIC")
api_secret = os.getenv("MJ_APIKEY_PRIVATE")

mailjet = Client(auth=(api_key, api_secret), version='v3.1')

data = {
  'Messages': [
    {
      "From": {
        "Email": os.getenv("AFSENDER_EMAIL"),
        "Name": "AktieBot"
      },
      "To": [
        {
          "Email": os.getenv("MODTAGER_EMAIL"),
          "Name": "Modtager"
        }
      ],
      "Subject": "Test af Mailjet 🔧",
      "TextPart": "Hej! Det her er en testmail fra din Python-integration 🚀",
      "HTMLPart": "<h3>Hej! 🚀</h3><p>Testmail fra din Python-integration med Mailjet virker!</p>"
    }
  ]
}

result = mailjet.send.create(data=data)
print(result.status_code)
print(result.json())
