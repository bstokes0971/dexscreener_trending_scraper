# DexScreener Trending Scraper

Scrapes DexScreener for 6hr trending tokens and returns this data in a csv. 

## Features
- Real-time scraping of DexScreener trending page
- Detailed token information including price, volume, and market cap

## Setup
1. Clone the repository
```bash
git clone https://github.com/bstokes0971/dexscreener_trending_scraper.git
```

2. Install requirements

```bash
cd dexscreener_trending_scraper
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. Run the script
```bash
python dexscreener_trending_scraper.py
```

