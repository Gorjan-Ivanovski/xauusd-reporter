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


def generate_and_save():
    """Fetch live data and regenerate HTML with AEST timestamps."""
    global latest_indicators, last_update
    
    try:
        logger.info("Fetching live data from TwelveData...")
        indicators = fetch_all_live()
        price = indicators.get('current_price', 0)
        
        generator = ReportGenerator()
        html = generator.generate(indicators, {})
        
        # Use AEST for all timestamps
        now_aest = datetime.now(AEST)
        now_utc = datetime.now(pytz.utc)
        html = html.replace('Saturday, May 16, 2026', now_aest.strftime('%A, %B %d, %Y'))
        
        # Add visible AEST timestamp with LIVE or FALLBACK indicator
        source = indicators.get('source', 'unknown')
        source_label = "LIVE" if source == 'twelvedata.com' else f"FALLBACK ({source})"
        old_footer = 'XAU/USD Daily Reporter | Auto-refreshes every hour'
        new_footer = f'XAU/USD Daily Reporter | Last Updated: {now_aest.strftime("%H:%M")} AEST ({now_utc.strftime("%H:%M")} UTC) | {source_label} | Source: {source}'
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
        return False


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
    return jsonify({
        'price': latest_indicators.get('current_price'),
        'change': latest_indicators.get('daily_change'),
        'change_pct': latest_indicators.get('daily_change_pct'),
        'last_update': last_update,
    })


@app.route('/api/status')
def api_status():
    """Health check with API key status."""
    from app.twelvedata_fetcher import get_api_key
    key = get_api_key()
    return jsonify({
        'status': 'ok',
        'price': latest_indicators.get('current_price'),
        'source': latest_indicators.get('source', 'unknown'),
        'last_update': last_update,
        'api_key_set': bool(key),
        'api_key_preview': key[:8] + '...' if key else 'NOT SET',
    })


@app.route('/trigger-update')
def trigger_update():
    """Force a data refresh."""
    success = generate_and_save()
    return jsonify({'success': success, 'price': latest_indicators.get('current_price'), 'last_update': last_update})


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
