import requests
import smtplib
import os
import dotenv
from email.mime.text import MIMEText
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from twilio.rest import Client
from bs4 import BeautifulSoup
import time

dotenv.load_dotenv()

# Twilio instellingen
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
RECIPIENT_PHONE_NUMBER = os.getenv("RECIPIENT_PHONE_NUMBER")

# Notificaties instellen
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_RECEIVER = "michiel.lok@gmail.com"
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Vluchtcriteria
FLIGHT_CRITERIA = {
    "origin": "AMS",
    "destination": "DPS",
    "depart_date": "2025-07-28",
    "return_date": "2025-08-17",
    "adults": 2,
    "children": 1,
    "cabin_class": "economy",
    "currency": "EUR",
    "max_price": 1500,
    "max_stops": 1,
    "max_duration": 19
}

# Lijst van websites om te scrapen
SCRAPE_SITES = [
    "https://www.skyscanner.nl",
    "https://www.google.com/travel/flights",
    "https://www.kayak.nl",
    "https://www.momondo.nl",
    "https://www.expedia.nl",
    "https://www.klm.com",
    "https://www.qatarairways.com",
    "https://www.emirates.com",
    "https://www.singaporeair.com",
    "https://www.lufthansa.com",
    "https://www.turkishairlines.com",
    "https://www.etihad.com"
    "https://www.gotogate.nl/"
]

# Scraper functie (vereenvoudigde versie, sommige websites hebben anti-scraping maatregelen)
def scrape_flight_prices():
    results = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for site in SCRAPE_SITES:
        try:
            response = requests.get(site, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # Dit is een placeholder. Elke site heeft een unieke manier om prijzen te tonen.
                price = None  # Scrape hier de daadwerkelijke prijs
                airline = None  # Scrape hier de luchtvaartmaatschappij
                if price and price <= FLIGHT_CRITERIA["max_price"]:
                    results.append({"site": site, "price": price, "airline": airline})
        except requests.exceptions.RequestException:
            continue
    return results

# Notificatie functies
def send_email_notification(message):
    msg = MIMEText(message)
    msg['Subject'] = "Goedkope vlucht gevonden!"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

def send_sms_notification(message):
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=RECIPIENT_PHONE_NUMBER
    )

# Hoofdscript
def main():
    st.title("Flight Price Tracker")
    results = scrape_flight_prices()
    
    if not results:
        st.warning("Geen goedkope vluchten gevonden.")
    else:
        df = pd.DataFrame(results)
        st.table(df)
        cheapest = min(results, key=lambda x: x["price"])
        notification_message = f"Goedkope vlucht gevonden! {cheapest['airline']} voor €{cheapest['price']} via {cheapest['site']}"
        send_email_notification(notification_message)
        send_sms_notification(notification_message)

if __name__ == "__main__":
    main()

