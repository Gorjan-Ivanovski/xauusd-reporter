"""GoldAPI.io data fetcher for live gold and precious metals prices."""
import requests
from datetime import datetime
from typing import Dict, Optional
from loguru import logger

import os

API_KEY = os.getenv('GOLDAPI_KEY', 'goldapi-9d90dfd0fb5478f8719751976d3d84a6-io')
BASE_URL = "https://www.goldapi.io/api"

HEADERS = {
    "x-access-token": API_KEY,
    "Content-Type": "application/json"
}


def fetch_gold_usd() -> Optional[Dict]:
    """Fetch live XAU/USD price from GoldAPI."""
    try:
        r = requests.get(f"{BASE_URL}/XAU/USD", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return {
                'current_price': float(data['price']),
                'daily_change': float(data['ch']),
                'daily_change_pct': float(data['chp']),
                'open': float(data['open_price']),
                'high': float(data['high_price']),
                'low': float(data['low_price']),
                'prev_close': float(data['prev_close_price']),
                'bid': float(data['bid']),
                'ask': float(data['ask']),
                'timestamp': int(data['timestamp']),
                'source': 'goldapi.io',
                'symbol': data.get('symbol', 'XAUUSD'),
            }
        else:
            logger.warning(f"GoldAPI returned status {r.status_code}: {r.text[:200]}")
            return None
    except Exception as e:
        logger.warning(f"GoldAPI fetch error: {e}")
        return None


def fetch_silver_usd() -> Optional[Dict]:
    """Fetch live XAG/USD price."""
    try:
        r = requests.get(f"{BASE_URL}/XAG/USD", headers=HEADERS, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return {
                'current_price': float(data['price']),
                'daily_change': float(data['ch']),
                'daily_change_pct': float(data['chp']),
                'timestamp': int(data['timestamp']),
            }
        return None
    except Exception as e:
        logger.warning(f"Silver fetch error: {e}")
        return None


def fetch_all_live() -> Dict:
    """Fetch all live data from GoldAPI + fallbacks."""
    logger.info("Fetching live data from GoldAPI...")
    
    indicators = {}
    
    # Primary: Gold price
    gold = fetch_gold_usd()
    if gold:
        indicators.update(gold)
        # Calculate derived values
        indicators['ath'] = 5645.60  # Keep ATH reference
        indicators['pct_from_ath'] = ((gold['current_price'] / 5645.60) - 1) * 100
        
        # Approximate levels from live data
        price = gold['current_price']
        indicators['pivot'] = (gold['high'] + gold['low'] + gold['prev_close']) / 3
        indicators['r1'] = 2 * indicators['pivot'] - gold['low']
        indicators['r2'] = indicators['pivot'] + (gold['high'] - gold['low'])
        indicators['s1'] = 2 * indicators['pivot'] - gold['high']
        indicators['s2'] = indicators['pivot'] - (gold['high'] - gold['low'])
        indicators['s3'] = indicators['s2'] - (gold['high'] - gold['low'])
        indicators['r3'] = indicators['r2'] + (gold['high'] - gold['low'])
        
        # ATR estimate from today's range
        indicators['atr_14'] = gold['high'] - gold['low']
        
        logger.info(f"Live gold: ${price:.2f} ({gold['daily_change']:+.2f}, {gold['daily_change_pct']:+.2f}%)")
    else:
        logger.warning("GoldAPI failed, using fallback data")
        indicators = get_fallback_data()
    
    # Silver
    silver = fetch_silver_usd()
    if silver:
        indicators['silver'] = silver['current_price']
        if indicators.get('current_price'):
            indicators['gold_silver_ratio'] = indicators['current_price'] / silver['current_price']
    
    # Static/research-based indicators (GoldAPI doesn't provide these)
    indicators['rsi'] = 35.42
    indicators['adx'] = 46.6
    indicators['macd'] = -26.31
    indicators['dxy'] = 99.27
    indicators['dxy_change'] = 0.15
    indicators['ten_year'] = 4.46
    indicators['vix'] = 18.5
    indicators['usd_jpy'] = 159.00
    indicators['oil'] = 103.67
    indicators['sma_200'] = 4359
    
    return indicators


def get_fallback_data() -> Dict:
    """Return research-based fallback data."""
    return {
        'current_price': 4540.00,
        'daily_change': -32.50,
        'daily_change_pct': -0.71,
        'ath': 5645.60,
        'pct_from_ath': -19.6,
        'open': 4540.58,
        'high': 4555.22,
        'low': 4480.43,
        'prev_close': 4540.58,
        'bid': 4537.15,
        'ask': 4538.25,
        'rsi': 35.42,
        'adx': 46.6,
        'macd': -26.31,
        'dxy': 99.27,
        'dxy_change': 0.15,
        'ten_year': 4.46,
        'vix': 18.5,
        'usd_jpy': 159.0,
        'oil': 103.67,
        'pivot': 4557,
        'r1': 4633,
        'r2': 4725,
        'r3': 4785,
        's1': 4480,
        's2': 4420,
        's3': 4328,
        'sma_200': 4359,
        'atr_14': 95,
        'source': 'fallback',
    }
