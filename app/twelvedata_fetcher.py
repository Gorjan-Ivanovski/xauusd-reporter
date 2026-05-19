"""TwelveData API fetcher for live gold and market data."""
import os
import requests
from datetime import datetime
from typing import Dict, Optional
from loguru import logger

BASE_URL = "https://api.twelvedata.com"


def get_api_key() -> str:
    """Read API key fresh from environment each time."""
    return os.getenv('TWELVEDATA_API_KEY', '').strip()


def fetch_gold_usd() -> Optional[Dict]:
    """Fetch live XAU/USD price from TwelveData."""
    api_key = get_api_key()
    
    if not api_key:
        logger.error("TWELVEDATA_API_KEY is not set! Add it as an environment variable.")
        return None
    
    logger.info(f"Using TwelveData API key: {api_key[:8]}...")
    
    try:
        url = f"{BASE_URL}/quote"
        params = {
            "symbol": "XAU/USD",
            "apikey": api_key,
        }
        logger.info(f"Requesting: {url}?symbol=XAU/USD")
        r = requests.get(url, params=params, timeout=15)
        
        logger.info(f"TwelveData response status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            logger.info(f"TwelveData raw response: {str(data)[:300]}")
            
            if 'price' in data:
                price = float(data['price'])
                prev_close = float(data.get('previous_close', data.get('close', price)))
                change = price - prev_close
                change_pct = (change / prev_close) * 100 if prev_close else 0
                
                result = {
                    'current_price': price,
                    'daily_change': change,
                    'daily_change_pct': change_pct,
                    'open': float(data.get('open', 0)),
                    'high': float(data.get('high', 0)),
                    'low': float(data.get('low', 0)),
                    'prev_close': prev_close,
                    'bid': price - 0.5,
                    'ask': price + 0.5,
                    'timestamp': int(datetime.now().timestamp()),
                    'source': 'twelvedata.com',
                    'symbol': 'XAU/USD',
                }
                logger.info(f"SUCCESS: Live gold ${price:.2f} (chg: {change:+.2f})")
                return result
            elif 'code' in data and data.get('status') == 'error':
                logger.error(f"TwelveData API error: {data.get('message', data)}")
                return None
            else:
                logger.warning(f"TwelveData response missing 'price' field. Keys: {list(data.keys())}")
                return None
        else:
            logger.error(f"TwelveData HTTP {r.status_code}: {r.text[:300]}")
            return None
    except Exception as e:
        logger.error(f"TwelveData fetch exception: {e}")
        return None


def fetch_all_live() -> Dict:
    """Fetch all live data from TwelveData + fallbacks."""
    logger.info("=== FETCHING LIVE DATA ===")
    
    indicators = {}
    
    # Primary: Gold price from TwelveData
    gold = fetch_gold_usd()
    if gold:
        indicators.update(gold)
        price = gold['current_price']
        indicators['ath'] = 5645.60
        indicators['pct_from_ath'] = ((price / 5645.60) - 1) * 100
        
        # Calculate levels from live data
        high = gold.get('high', price * 1.005)
        low = gold.get('low', price * 0.995)
        prev = gold.get('prev_close', price)
        
        pivot = (high + low + prev) / 3
        indicators['pivot'] = pivot
        indicators['r1'] = 2 * pivot - low
        indicators['r2'] = pivot + (high - low)
        indicators['r3'] = indicators['r2'] + (high - low)
        indicators['s1'] = 2 * pivot - high
        indicators['s2'] = pivot - (high - low)
        indicators['s3'] = indicators['s2'] - (high - low)
        indicators['atr_14'] = high - low
        
        logger.info(f"LIVE DATA: ${price:.2f} | source: twelvedata.com")
    else:
        logger.error("TWELVEDATA FAILED — using FALLBACK data (price will be stale!)")
        indicators = get_fallback_data()
    
    # Static/research-based indicators (TwelveData free tier doesn't provide these)
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
    """Return research-based fallback data — STALE, only used when API fails."""
    logger.warning("RETURNING FALLBACK DATA — price is NOT live!")
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
