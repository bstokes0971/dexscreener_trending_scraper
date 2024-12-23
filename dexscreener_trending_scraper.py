from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import Driver
import pandas as pd
import time
import re

def clean_token_name(token_parts):
    """Clean and combine token parts"""
    # Filter out known chains and separators
    non_token_parts = ['/', 'SOL', 'WETH', 'SUI', 'wS']
    token = [part for part in token_parts if part not in non_token_parts]
    return ' '.join(token)

def get_chain(parts):
    """Extract chain info"""
    chains = ['SOL', 'WETH', 'SUI', 'wS']
    for part in parts:
        if part in chains:
            return part
    return 'SOL'  # Default to SOL if no chain found

def preprocess_row_data(row_data):
    """Preprocess and clean row data"""
    # Remove empty strings and numeric-only items that might be supply numbers
    cleaned = []
    for item in row_data:
        item = item.strip()
        if item and not (item.isdigit() and len(item) >= 3):
            cleaned.append(item)
    return cleaned

def normalize_row_data(row_data):
    """Normalize row data to ensure consistent column ordering"""
    cleaned = preprocess_row_data(row_data)
    
    try:
        # Extract rank
        rank = cleaned[0].replace('#', '')
        
        # Get token and chain info - look at all parts before first $ value
        token_parts = []
        chain = 'SOL'
        for part in cleaned[1:]:
            if part.startswith('$'):
                break
            token_parts.append(part)
        
        token = clean_token_name(token_parts)
        chain = get_chain(token_parts)
        
        # Find price and market cap (last two $ values)
        dollar_values = [x for x in cleaned if x.startswith('$')]
        price = None
        mcap = None
        if len(dollar_values) >= 2:
            price = dollar_values[0]
            mcap = dollar_values[-1]
        elif len(dollar_values) == 1:
            price = dollar_values[0]
        
        # Look for age (must match valid patterns)
        age = None
        age_pattern = r'^\d+[hmdw]$|^\d+mo$'
        for item in cleaned:
            if re.match(age_pattern, item):
                age = item
                break
        
        # Extract txns (comma-separated number)
        txns = None
        for item in cleaned:
            if ',' in item and all(c.isdigit() or c == ',' for c in item):
                txns = item
                break
        
        # Find volume ($ value with K/M/B)
        volume = None
        for item in dollar_values:
            if any(x in item for x in ['K', 'M', 'B']):
                volume = item
                break
        
        # Get makers count
        makers = None
        for item in cleaned:
            if item.isdigit() and len(item) <= 4:
                if item != rank and item != txns:
                    makers = item
                    break
        
        # Extract percentage changes
        percentages = []
        for item in cleaned:
            if '%' in item:
                value = item.replace('%', '').replace(',', '')
                if value.replace('.', '').replace('-', '').isdigit():
                    percentages.append(value)
        
        m5, h1, h6, h24 = [''] * 4
        if len(percentages) >= 4:
            m5, h1, h6, h24 = percentages[:4]
        
        # Find liquidity ($ value near end, before mcap)
        liquidity = None
        for val in reversed(dollar_values[:-1]):  # Exclude last value (mcap)
            if val != price:
                liquidity = val
                break
        
        return {
            'Rank': rank,
            'Token': token.strip(),
            'Chain': chain,
            'Price': price or '',
            'Age': age or '',
            'Txns': txns or '',
            'Volume': volume or '',
            'Makers': makers or '',
            '5m': m5 or '',
            '1h': h1 or '',
            '6h': h6 or '',
            '24h': h24 or '',
            'Liquidity': liquidity or '',
            'Market_Cap': mcap or ''
        }
        
    except Exception as e:
        print(f"Error normalizing row: {e}")
        print(f"Raw data: {cleaned}")
        return None

def scrape_dex_table():
    driver = Driver(uc=True)
    driver.set_window_size(1920, 1080)
    
    try:
        driver.get("https://dexscreener.com/")
        time.sleep(5)
        
        rows = WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "ds-dex-table-row-top"))
        )
        
        print(f"Found {len(rows)} rows")
        
        data = []
        for row in rows:
            try:
                elements = row.find_elements(By.XPATH, ".//*[text()]")
                row_data = [elem.text for elem in elements]
                
                normalized_data = normalize_row_data(row_data)
                if normalized_data:
                    data.append(normalized_data)
                    print(f"Processed token: {normalized_data['Token']}")
                
            except Exception as e:
                print(f"Error processing row: {str(e)}")
                continue
        
        if data:
            df = pd.DataFrame(data)
            df.to_csv("dex_data_raw.csv", index=False)
            print("\nData saved successfully!")
            print("\nFirst few rows:")
            print(df.head())
            return df
            
    except Exception as e:
        print(f"Major error occurred: {str(e)}")
        if 'data' in locals() and data:
            pd.DataFrame(data).to_csv("dex_data_emergency.csv", index=False)
            print("Emergency data save completed")
        return None
        
    finally:
        driver.save_screenshot("debug_screenshot.png")
        driver.quit()

if __name__ == "__main__":
    df = scrape_dex_table()    
        