import requests
import sqlite3
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from twilio.rest import Client
from bs4 import BeautifulSoup
import time

# Twilio instellingen
TWILIO_SID = "YOUR_TWILIO_SID"
TWILIO_AUTH_TOKEN = "YOUR_TWILIO_AUTH_TOKEN"
TWILIO_PHONE_NUMBER = "YOUR_TWILIO_PHONE_NUMBER"
RECIPIENT_PHONE_NUMBER = "YOUR_PHONE_NUMBER"

# Skyscanner API instellingen (gebruik een API-key van RapidAPI)
API_KEY = "YOUR_API_KEY"
API_URL = "https://partners.api.skyscanner.net/apiservices/browseroutes/v1.0/NL/EUR/en-US/{origin}/{destination}/{date}?apiKey=" + API_KEY

# Websites voor web scraping
FLIGHT_WEBSITES = [
    "https://www.skyscanner.nl",
    "https://www.kayak.nl",
    "https://www.google.com/flights",
    "https://www.expedia.nl",
    "https://www.cheaptickets.nl",
    "https://www.momondo.nl",
    "https://www.orbitz.com",
    "https://www.priceline.com",
    "https://www.travelocity.com",
    "https://www.hotwire.com",
    "https://www.edreams.com",
    "https://www.opodo.com",
    "https://www.justfly.com",
    "https://www.trip.com",
    "https://www.vliegtickets.nl"
]

# Vluchtdata instellingen
FLIGHTS = [
    {"origin": "AMS", "destination": "DPS", "date": "2025-07-28"},
    {"origin": "AMS", "destination": "DEN", "date": "2025-05-25"},
]

# Database instellen
DB_NAME = "flight_prices.db"

def create_database():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin TEXT,
            destination TEXT,
            date TEXT,
            price INTEGER,
            source TEXT,
            checked_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# Ophalen van vluchtprijzen via API
def get_flight_price(origin, destination, date):
    url = API_URL.format(origin=origin, destination=destination, date=date)
    response = requests.get(url)
    data = response.json()
    
    if "Quotes" in data and data["Quotes"]:
        return data["Quotes"][0]["MinPrice"], "Skyscanner API"
    return None, None

# Scraping van vluchtprijzen
def scrape_flight_prices():
    prices = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for site in FLIGHT_WEBSITES:
        try:
            response = requests.get(site, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            price_tag = soup.find(class_="price")  # Dit is een placeholder, CSS-selectors verschillen per site
            
            if price_tag:
                price = int(price_tag.text.replace("€", "").replace(",", ""))
                prices.append((site, price))
        except Exception as e:
            print(f"Fout bij scrapen van {site}: {e}")
    return prices

# Opslaan en vergelijken van prijzen
def check_and_store_price(origin, destination, date):
    price, source = get_flight_price(origin, destination, date)
    if price is None:
        scraped_prices = scrape_flight_prices()
        for site, scraped_price in scraped_prices:
            store_price(origin, destination, date, scraped_price, site)
    else:
        store_price(origin, destination, date, price, source)

# Opslag in database
def store_price(origin, destination, date, price, source):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("SELECT price FROM prices WHERE origin=? AND destination=? AND date=? ORDER BY checked_at DESC LIMIT 1", 
              (origin, destination, date))
    last_price = c.fetchone()
    
    if last_price and abs(last_price[0] - price) >= 50:
        send_alerts(origin, destination, date, last_price[0], price)
    
    c.execute("INSERT INTO prices (origin, destination, date, price, source, checked_at) VALUES (?, ?, ?, ?, ?, ?)",
              (origin, destination, date, price, source, datetime.now()))
    conn.commit()
    conn.close()
    st.success(f"{origin} -> {destination} op {date} ({source}): €{price}")

# Prijsverloop weergeven
def plot_price_trends():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM prices", conn)
    conn.close()
    
    if df.empty:
        st.warning("Nog geen prijsdata beschikbaar.")
        return
    
    df["checked_at"] = pd.to_datetime(df["checked_at"])
    df = df.sort_values("checked_at")
    
    fig, ax = plt.subplots()
    for (origin, destination, source), group in df.groupby(["origin", "destination", "source"]):
        ax.plot(group["checked_at"], group["price"], marker="o", label=f"{origin} -> {destination} ({source})")
    
    ax.set_title("Prijsverloop van vluchten")
    ax.set_xlabel("Datum")
    ax.set_ylabel("Prijs (€)")
    ax.legend()
    st.pyplot(fig)

# Hoofdscript
def main():
    st.title("Flight Price Tracker")
    create_database()
    for flight in FLIGHTS:
        check_and_store_price(flight["origin"], flight["destination"], flight["date"])
    
    plot_price_trends()

if __name__ == "__main__":
    main()
