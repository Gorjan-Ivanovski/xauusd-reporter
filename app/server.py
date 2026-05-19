"""Web server + background updater for XAU/USD Dashboard on Railway."""
from flask import Flask, send_file, jsonify
from threading import Thread
import time
import os
import sys
from datetime import datetime
from loguru import logger

# Setup paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from app.goldapi_fetcher import fetch_all_live
from app.report_generator import ReportGenerator

app = Flask(__name__)
WEB_DIR = os.path.join(PROJECT_ROOT, 'web')

# State
latest_indicators = {}
last_update = "Never"


def generate_and_save():
    """Fetch live data and regenerate HTML."""
    global latest_indicators, last_update
    
    try:
        logger.info("Fetching live GoldAPI data...")
        indicators = fetch_all_live()
        price = indicators.get('current_price', 0)
        
        generator = ReportGenerator()
        html = generator.generate(indicators, {})
        
        now = datetime.now()
        html = html.replace('Saturday, May 16, 2026', now.strftime('%A, %B %d, %Y'))
        
        # Add visible timestamp
        old_footer = 'XAU/USD Daily Reporter | Auto-refreshes every hour'
        new_footer = f'XAU/USD Daily Reporter | Last Updated: {now.strftime("%H:%M")} UTC | Source: GoldAPI.io'
        html = html.replace(old_footer, new_footer)
        
        os.makedirs(WEB_DIR, exist_ok=True)
        with open(os.path.join(WEB_DIR, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        
        latest_indicators = indicators
        last_update = now.strftime('%Y-%m-%d %H:%M:%S UTC')
        
        logger.info(f"Updated: ${price:.2f} at {last_update}")
        return True
    except Exception as e:
        logger.error(f"Update error: {e}")
        return False


def background_updater():
    """Update data every 5 minutes during market hours."""
    logger.info("Background updater started")
    generate_and_save()  # Initial update
    
    last_minute = None
    
    while True:
        try:
            now = datetime.now()
            minute = now.minute
            
            # Every 5 minutes during market hours (Mon-Fri 8-18)
            if now.weekday() < 5 and 8 <= now.hour <= 18:
                if minute % 5 == 0 and minute != last_minute:
                    logger.info(f"Market hours update at {now.strftime('%H:%M')}")
                    generate_and_save()
                    last_minute = minute
            
            time.sleep(30)
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
    """Health check."""
    return jsonify({
        'status': 'ok',
        'price': latest_indicators.get('current_price'),
        'last_update': last_update,
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
