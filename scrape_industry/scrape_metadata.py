"""Scrape stock metadata."""

import csv
import pandas as pd
import requests

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options


def main():
    """Input must be CSV file with stock symbols in the zero index."""
    stock_symbol_filepath: str = "./us_tickers.csv"
    output_metadata_filepath: str = "./new_columns_to_add.csv"
    
    driver = create_webdriver()
    
    # Get list of cleaned stock symbols 
    with open(stock_symbol_filepath, "r") as symbol_file, open(output_metadata_filepath, "w") as output_file:
        csv_reader = csv.reader(symbol_file, delimiter=",")

        writer = csv.DictWriter(output_file, fieldnames=["symbol", "sector", "industry", "description", "website"])
        writer.writeheader()
        
        for line_symbol in csv_reader:
            symbol = line_symbol[0]
            
            page_result: tuple[str, str, str, str] = get_yahoo_data(driver, symbol)
            new_row = { 
                        "symbol": symbol, 
                        "sector": page_result[0], 
                        "industry": page_result[1],
                        "description": page_result[2],
                        "website": page_result[3]
                      }
            
            print(new_row)
            writer.writerow(new_row)    
    
    
def get_yahoo_data(driver: webdriver, symbol: str) -> tuple[str, str, str, str]:
    """Scrape from Yahoo Finance."""  
    sector_element = industry_element = desc_element = website_element = ""

    try: 
        driver.get(f"https://finance.yahoo.com/quote/{symbol}/profile?p={symbol}")
    except KeyboardInterrupt as ke:
        driver.close()
    except TimeoutException as te:
        print(te)

    try:
        select = "#Col1-0-Profile-Proxy > section > div.asset-profile-container > div > div > p.D\(ib\).Va\(t\) > span:nth-child(2)"
        sector_element = driver.find_element(By.CSS_SELECTOR, select).text
    except NoSuchElementException:
        print(f"No element found for {symbol} sector")

    try:
        select = "#Col1-0-Profile-Proxy > section > div.asset-profile-container > div > div > p.D\(ib\).Va\(t\) > span:nth-child(5)"
        industry_element = driver.find_element(By.CSS_SELECTOR, select).text
    except NoSuchElementException:
        print(f"No element found for {symbol} industry")
    
    try:
        select = "#Col1-0-Profile-Proxy > section > section.quote-sub-section.Mt\(30px\) > p"
        desc_element = driver.find_element(By.CSS_SELECTOR, select).text
    except NoSuchElementException:
        print(f"No element found for {symbol} description")

    try:
        select = "#Col1-0-Profile-Proxy > section > div.asset-profile-container > div > div > p.D\(ib\).W\(47\.727\%\).Pend\(40px\) > a:nth-child(6)"
        website_element = driver.find_element(By.CSS_SELECTOR, select).text
    except NoSuchElementException:
        print(f"No element found for {symbol} website")
    
    return (sector_element, industry_element, desc_element, website_element)


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