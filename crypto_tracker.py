"""
Cryptocurrency Price Tracker
Scrapes top 10 coins from CoinMarketCap using Selenium and saves to CSV.
"""

import os
import time
from datetime import datetime

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


CSV_FILENAME = "crypto_prices.csv"
URL = "https://coinmarketcap.com/"


def get_driver(headless: bool = True):
    """Launch and return a configured Chrome WebDriver."""
    
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def scrape_top_coins(driver, num_coins: int = 10):
    """Scrape name, price, 24h change, and market cap for the top N coins."""
    driver.get(URL)
    time.sleep(6)  # allow JS-rendered content to load

    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    if not rows:
        print("No rows found. The site structure may have changed — "
              "inspect the page and update the selectors below.")
        return []

    coins_data = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for row in rows[:num_coins]:
        try:
            cells = row.find_elements(By.TAG_NAME, "td")
            # Column positions can shift if CMC changes its layout —
            # inspect the page (right-click > Inspect) and adjust indices if needed.
            name = cells[2].text.split("\n")[0].strip()
            price = cells[3].text.strip()
            change_24h = cells[4].text.strip()
            market_cap = cells[7].text.strip()

            coins_data.append({
                "Coin": name,
                "Price": price,
                "24h Change": change_24h,
                "Market Cap": market_cap,
                "Timestamp": timestamp,
            })
        except (IndexError, Exception) as e:
            print(f"Skipping a row due to error: {e}")
            continue

    return coins_data


def save_to_csv(data, filename: str = CSV_FILENAME):
    """Append data to CSV (creates the file with headers if it doesn't exist)."""
    if not data:
        print("No data to save.")
        return
    df = pd.DataFrame(data)
    file_exists = os.path.isfile(filename)
    df.to_csv(filename, mode="a" if file_exists else "w", header=not file_exists, index=False)
    print(f"Saved {len(data)} rows to '{filename}'.")


def filter_coins(data, min_price=None, max_price=None, top_gainers=False):
    """Optional: filter coins by price range or sort by top gainers."""
    df = pd.DataFrame(data)
    if df.empty:
        return df

    def clean_price(p):
        return float(p.replace("$", "").replace(",", ""))

    df["_price_num"] = df["Price"].apply(clean_price)

    if min_price is not None:
        df = df[df["_price_num"] >= min_price]
    if max_price is not None:
        df = df[df["_price_num"] <= max_price]
    if top_gainers:
        df["_change_num"] = df["24h Change"].str.replace("%", "").astype(float)
        df = df.sort_values(by="_change_num", ascending=False)
        df = df.drop(columns=["_change_num"])

    return df.drop(columns=["_price_num"])


if __name__ == "__main__":
    driver = get_driver(headless=False)  # set headless=False to watch the browser
    try:
        print("Scraping CoinMarketCap top 10 coins...")
        data = scrape_top_coins(driver, num_coins=10)

        if data:
            save_to_csv(data)
            print("\nScraped Data:")
            print(pd.DataFrame(data).to_string(index=False))

            # Example optional filter usage:
            gainers = filter_coins(data, top_gainers=True)
            print("\nTop Gainers:")
            print(gainers.to_string(index=False))
            gainers.to_csv("top_gainers.csv", index=False)
        else:
            print("No data scraped. Check selectors / site structure.")
    finally:
        driver.quit()
        print("\nBrowser closed. Done.")