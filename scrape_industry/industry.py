"""Scrape stock metadata from Nasdaq."""

import csv
import pandas as pd
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome import options as chrome_options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options


def main():
    nasdaq_df = get_stonks()
    driver = create_webdriver()

    with open("stock_industry.csv", "w") as file:
        writer = csv.DictWriter(file, fieldnames=["symbol", "sector", "industry"])
        writer.writeheader()
        
        for symbol in nasdaq_df["symbol"]:
            if "^" not in symbol:
                page_result: tuple[str, str] = get_industry(driver, symbol)
                writer.writerow({ "symbol": symbol, "sector": page_result[0], "industry": page_result[1] })    
    
    
def get_industry(driver: webdriver, symbol: str) -> tuple[str, str]:
    sector_element = ""
    industry_element = ""

    try: 
        driver.get(f"https://finance.yahoo.com/quote/{symbol}/profile?p={symbol}")
    except KeyboardInterrupt as ke:
        driver.close()
    except TimeoutException as te:
        print(te)

    try:
        sector_select = "#Col1-0-Profile-Proxy > section > div.asset-profile-container > div > div > p.D\(ib\).Va\(t\) > span:nth-child(2)"
        sector_element = driver.find_element(By.CSS_SELECTOR, sector_select).text
    except NoSuchElementException as nse:
        print(f"No element found for {symbol} sector")

    try:
        industry_select = "#Col1-0-Profile-Proxy > section > div.asset-profile-container > div > div > p.D\(ib\).Va\(t\) > span:nth-child(5)"
        industry_element = driver.find_element(By.CSS_SELECTOR, industry_select).text
    except NoSuchElementException as nse:
        print(f"No element found for {symbol} industry")
    
    return (sector_element, industry_element)


def create_webdriver() -> webdriver:
    options = Options()
    # Remove bot-like qualities
    options.add_experimental_option(
        "excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("window-size=1280,800")
    options.add_argument("disable-infobars")  # disabling infobars
    options.add_argument("--disable-extensions")  # disabling extensions
    options.add_argument("--disable-dev-shm-usage") # overcome limited resource problems
    options.add_argument("--no-sandbox")  # Bypass OS security model
    options.add_argument("--headless")

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(2)
    print(f"CHROME BROWSER SESSION ID: {driver.session_id}")

    return driver


def get_stonks() -> pd.DataFrame:
    headers = {
        "User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:84.0) Gecko/20100101 Firefox/84.0",
    }

    # Get latest daily data for stocks
    response: requests.Response = requests.get(
        "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=99999&exchange=nyse",
        headers=headers)
    
    nasdaq_df = pd.json_normalize(response.json(), record_path=["data", "table", "rows"])
    return nasdaq_df


if __name__ == "__main__":
    main()