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

# Skyscanner API instellingen
API_URL = "https://skyscanner89.p.rapidapi.com/flights/one-way/list"
API_HEADERS = {
    "x-rapidapi-host": "skyscanner89.p.rapidapi.com",
    "x-rapidapi-key": "75068b0d81msh6f2ac0750ffe789p1edffejsn99091da45b17"
}

# Correcte locatie-ID's voor AMS en DPS
LOCATION_IDS = {
    "AMS": "95565044",  # Amsterdam Schiphol
    "DPS": "95673809"   # Denpasar (Bali)
}

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
    """Haalt vluchtprijzen op met de correcte locatie-ID's."""
    origin_id = LOCATION_IDS.get(origin)
    destination_id = LOCATION_IDS.get(destination)
    if not origin_id or not destination_id:
        st.error(f"Geen locatie-ID gevonden voor {origin} of {destination}")
        return None, None
    
    params = {
        "date": date,
        "origin": origin,
        "originId": origin_id,
        "destination": destination,
        "destinationId": destination_id,
        "cabinClass": "economy",
        "adults": "1",
        "children": "0",
        "infants": "0",
        "locale": "nl-NL",
        "market": "NL",
        "currency": "EUR"
    }
    try:
        response = requests.get(API_URL, headers=API_HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            min_price = data["data"][0]["price"]
            return min_price, "Skyscanner API"
        else:
            st.error(f"Geen prijsgegevens gevonden voor {origin} -> {destination} op {date}")
            return None, None
    except requests.exceptions.RequestException as e:
        st.error(f"API-fout: {e}")
        return None, None
    except requests.exceptions.JSONDecodeError:
        st.error("Fout bij het decoderen van API-response. Mogelijk ongeldige API-key of limiet bereikt.")
        return None, None

# Opslaan en vergelijken van prijzen
def check_and_store_price(origin, destination, date):
    price, source = get_flight_price(origin, destination, date)
    if price is None:
        return
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    c.execute("SELECT price FROM prices WHERE origin=? AND destination=? AND date=? ORDER BY checked_at DESC LIMIT 1", 
              (origin, destination, date))
    last_price = c.fetchone()
    
    if last_price and abs(last_price[0] - price) >= 50:
        st.warning(f"Prijsverandering voor {origin} -> {destination}: van €{last_price[0]} naar €{price}")
    
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
