"""Web server + background updater for XAU/USD Dashboard on Railway."""
from flask import Flask, send_file, jsonify
from threading import Thread
import time
import os
import sys
from datetime import datetime
from loguru import logger
import pytz

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.twelvedata_fetcher import fetch_all_live
from app.report_generator import ReportGenerator

# AEST timezone
AEST = pytz.timezone('Australia/Sydney')

app = Flask(__name__)
WEB_DIR = os.path.join(PROJECT_ROOT, 'web')

# State
latest_indicators = {}
last_update = "Never"


def generate_error_page(reason: str) -> str:
    """Generate an error page when price data is unavailable."""
    now_aest = datetime.now(AEST)
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>XAU/USD - Error</title>
<style>
body {{ font-family: Arial, sans-serif; background: #1a1a2e; color: #fff; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }}
.container {{ text-align: center; max-width: 600px; padding: 40px; }}
h1 {{ color: #daa520; font-size: 48px; margin-bottom: 10px; }} 
.error {{ color: #ef4444; font-size: 24px; margin: 20px 0; }}
.reason {{ color: #888; font-size: 16px; margin: 15px 0; }}
.timestamp {{ color: #555; font-size: 14px; margin-top: 30px; }}
.retry {{ color: #22c55e; font-size: 14px; margin-top: 15px; }}
</style></head>
<body>
<div class="container">
<h1>XAU/USD</h1>
<div class="error">⚠ Price Unavailable</div>
<div class="reason">{reason}</div>
<div class="timestamp">{now_aest.strftime('%a %d %b %H:%M')} AEST</div>
<div class="retry">Retrying in 60 minutes...</div>
</div></body></html>"""


def generate_and_save():
    """Fetch live data and regenerate HTML with AEST timestamps."""
    global latest_indicators, last_update
    
    try:
        logger.info("Fetching live data from TwelveData...")
        indicators = fetch_all_live()
        price = indicators.get('current_price', 0)
        source = indicators.get('source', 'unknown')
        
        # Use AEST for all timestamps - now WITH date
        now_aest = datetime.now(AEST)
        now_utc = datetime.now(pytz.utc)
        
        # If data is from fallback, show error page instead of stale price
        if source == 'fallback':
            logger.error("Data source is FALLBACK — showing error page")
            html = generate_error_page(
                "Live price data unavailable. The TwelveData API may be down or the API key is invalid/expired."
            )
            os.makedirs(WEB_DIR, exist_ok=True)
            with open(os.path.join(WEB_DIR, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            last_update = now_aest.strftime('%Y-%m-%d %H:%M:%S AEST')
            logger.info(f"Error page saved at {last_update}")
            return False
        
        # LIVE data — recalculate technical levels from live price
        indicators = recalculate_analysis(indicators)
        
        generator = ReportGenerator()
        html = generator.generate(indicators, {})
        
        # Update date with AEST
        html = html.replace('Saturday, May 16, 2026', now_aest.strftime('%A, %B %d, %Y'))
        
        # Add visible AEST timestamp WITH date
        old_footer = 'XAU/USD Daily Reporter | Auto-refreshes every hour'
        new_footer = f'XAU/USD Daily Reporter | Last Updated: {now_aest.strftime("%a %d %b %H:%M")} AEST ({now_utc.strftime("%H:%M")} UTC) | LIVE | Source: twelvedata.com'
        html = html.replace(old_footer, new_footer)
        
        os.makedirs(WEB_DIR, exist_ok=True)
        with open(os.path.join(WEB_DIR, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        
        latest_indicators = indicators
        last_update = now_aest.strftime('%Y-%m-%d %H:%M:%S AEST')
        
        logger.info(f"Updated: ${price:.2f} at {last_update}")
        return True
    except Exception as e:
        logger.error(f"Update error: {e}")
        # Even on error, show error page
        try:
            html = generate_error_page(f"Server error: {str(e)}")
            with open(os.path.join(WEB_DIR, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
        except:
            pass
        return False


def recalculate_analysis(indicators: dict) -> dict:
    """Recalculate technical levels from live price data on every refresh."""
    price = indicators.get('current_price', 0)
    high = indicators.get('high', price)
    low = indicators.get('low', price)
    prev = indicators.get('prev_close', price)
    
    # Recalculate pivot and S/R from live data
    pivot = (high + low + prev) / 3
    atr = high - low if high and low else price * 0.01
    
    indicators['pivot'] = pivot
    indicators['r1'] = 2 * pivot - low
    indicators['r2'] = pivot + (high - low)
    indicators['r3'] = indicators['r2'] + atr * 0.5
    indicators['s1'] = 2 * pivot - high
    indicators['s2'] = pivot - (high - low)
    indicators['s3'] = indicators['s2'] - atr * 0.5
    indicators['atr_14'] = atr
    
    # Recalculate trend bias from price position relative to SMA
    sma_200 = indicators.get('sma_200', 4359)
    indicators['trend_bias'] = 'BULLISH' if price > sma_200 else 'BEARISH'
    
    # Update distance from ATH
    indicators['pct_from_ath'] = ((price / 5645.60) - 1) * 100
    
    logger.info(f"Recalculated levels: pivot=${pivot:.0f}, trend={indicators['trend_bias']}")
    return indicators


def background_updater():
    """Update data once per hour (60 min) — TwelveData API limit."""
    logger.info("Background updater started (AEST timezone)")
    generate_and_save()  # Initial update
    
    last_hour = None
    
    while True:
        try:
            now = datetime.now(AEST)
            hour = now.hour
            minute = now.minute
            
            # Update once per hour at :00 during market hours (Mon-Fri 8-18 AEST)
            if now.weekday() < 5 and 8 <= hour <= 18:
                if minute == 0 and hour != last_hour:
                    logger.info(f"Hourly update at {now.strftime('%H:%M')} AEST")
                    generate_and_save()
                    last_hour = hour
            else:
                # Off-hours: still update once per hour
                if minute == 0 and hour != last_hour:
                    logger.info(f"Off-hours update at {now.strftime('%H:%M')} AEST")
                    generate_and_save()
                    last_hour = hour
            
            time.sleep(60)  # Check every minute
        except Exception as e:
            logger.error(f"Updater error: {e}")
            time.sleep(60)


@app.route('/')
def dashboard():
    """Serve the main dashboard."""
    index_path = os.path.join(WEB_DIR, 'index.html')
    if os.path.exists(index_path):
        return send_file(index_path)
    return "Loading... please wait 30 seconds.", 503


@app.route('/api/price')
def api_price():
    """Current price as JSON."""
    source = latest_indicators.get('source', 'unknown')
    if source == 'fallback':
        return jsonify({
            'error': 'Price unavailable - API data not live',
            'source': source,
            'last_update': last_update,
        }), 503
    return jsonify({
        'price': latest_indicators.get('current_price'),
        'change': latest_indicators.get('daily_change'),
        'change_pct': latest_indicators.get('daily_change_pct'),
        'source': source,
        'last_update': last_update,
    })


@app.route('/api/status')
def api_status():
    """Health check with API key status."""
    from app.twelvedata_fetcher import get_api_key
    key = get_api_key()
    source = latest_indicators.get('source', 'unknown')
    return jsonify({
        'status': 'ok' if source == 'twelvedata.com' else 'error',
        'price': latest_indicators.get('current_price'),
        'source': source,
        'last_update': last_update,
        'api_key_set': bool(key),
        'api_key_preview': key[:8] + '...' if key else 'NOT SET',
    })


@app.route('/trigger-update')
def trigger_update():
    """Force a data refresh."""
    success = generate_and_save()
    return jsonify({
        'success': success,
        'price': latest_indicators.get('current_price'),
        'source': latest_indicators.get('source', 'unknown'),
        'last_update': last_update,
    })


def start():
    """Start server + background updater."""
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | {message}")
    
    Thread(target=background_updater, daemon=True).start()
    
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Server starting on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    start()
