import os
import time
import smtplib
import pandas as pd
import streamlit as st
from email.mime.text import MIMEText
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

# Notificatie instellingen
EMAIL_SENDER = "jouw-email@gmail.com"
EMAIL_RECEIVER = "michiel.lok@gmail.com"
EMAIL_PASSWORD = "jouw-wachtwoord"

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

# Websites om te scrapen
SCRAPE_SITES = {
    "Skyscanner": "https://www.skyscanner.nl",
    "Google Flights": "https://www.google.com/travel/flights",
    "Kayak": "https://www.kayak.nl",
    "Momondo": "https://www.momondo.nl"
}

# Selenium WebDriver configuratie
options = Options()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Scraper functie
def scrape_flight_prices():
    results = []
    for site_name, site_url in SCRAPE_SITES.items():
        try:
            driver.get(site_url)
            time.sleep(5)  # Wachten tot de pagina geladen is
            
            if "skyscanner" in site_url:
                prices = driver.find_elements(By.CLASS_NAME, "BpkText_bpk-text__NjFjy")  # Aanpassen voor echte selector
            elif "google" in site_url:
                prices = driver.find_elements(By.CLASS_NAME, "YMlKec")
            elif "kayak" in site_url:
                prices = driver.find_elements(By.CLASS_NAME, "price-text")
            elif "momondo" in site_url:
                prices = driver.find_elements(By.CLASS_NAME, "ticket-price")
            else:
                prices = []
            
            extracted_prices = [int(p.text.replace("€", "").replace(",", "")) for p in prices if p.text]
            if extracted_prices:
                min_price = min(extracted_prices)
                results.append({"site": site_name, "price": min_price})
        except Exception as e:
            print(f"Error scraping {site_name}: {e}")
    return results

# Notificatie functie
def send_email_notification(message):
    msg = MIMEText(message)
    msg['Subject'] = "Goedkope vlucht gevonden!"
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

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
        if cheapest["price"] < FLIGHT_CRITERIA["max_price"]:
            notification_message = f"Goedkope vlucht gevonden! {cheapest['site']} voor €{cheapest['price']}"
            send_email_notification(notification_message)

if __name__ == "__main__":
    main()
    driver.quit()


