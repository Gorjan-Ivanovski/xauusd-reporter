"""Web server + background updater + daily batch report for XAU/USD Dashboard."""
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

# AEST timezone
AEST = pytz.timezone('Australia/Sydney')

app = Flask(__name__)
WEB_DIR = os.path.join(PROJECT_ROOT, 'web')

# State
latest_indicators = {}
last_update = "Never"
last_full_report = "Never"


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
    """Hourly price update — lightweight, just price + levels."""
    global latest_indicators, last_update
    
    try:
        logger.info("[HOURLY] Fetching live data...")
        indicators = fetch_all_live()
        price = indicators.get('current_price', 0)
        source = indicators.get('source', 'unknown')
        now_aest = datetime.now(AEST)
        
        if source != 'twelvedata.com':
            logger.error("[HOURLY] FALLBACK data — showing error page")
            html = generate_error_page("Live price data unavailable. API key may be invalid.")
            os.makedirs(WEB_DIR, exist_ok=True)
            with open(os.path.join(WEB_DIR, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            last_update = now_aest.strftime('%Y-%m-%d %H:%M:%S AEST')
            return False
        
        indicators = recalculate_analysis(indicators)
        
        # ALWAYS use the dynamic batch report generator — never the old static template
        from app.batch_report import generate_full_report
        html = generate_full_report()
        
        if not html or len(html) < 1000:
            logger.error("[HOURLY] Batch report failed, falling back to error page")
            html = generate_error_page("Report generation failed")
            return False
        
        os.makedirs(WEB_DIR, exist_ok=True)
        with open(os.path.join(WEB_DIR, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html)
        
        latest_indicators = indicators
        last_update = now_aest.strftime('%Y-%m-%d %H:%M:%S AEST')
        logger.info(f"[HOURLY] Updated: ${price:.2f} at {last_update}")
        return True
    except Exception as e:
        logger.error(f"[HOURLY] Error: {e}")
        return False


def generate_full_report_job():
    """Daily 6 AM batch job — FULL analysis rewrite with fresh prices."""
    global last_full_report, latest_indicators, last_update
    
    now_aest = datetime.now(AEST)
    logger.info(f"[BATCH] === FULL DAILY REPORT START: {now_aest.strftime('%Y-%m-%d %H:%M')} AEST ===")
    logger.info("[BATCH] Rewriting ALL analysis: macro, technical, events, trade plan...")
    
    try:
        from app.batch_report import generate_full_report
        
        html = generate_full_report()
        
        if html and len(html) > 1000:
            os.makedirs(WEB_DIR, exist_ok=True)
            with open(os.path.join(WEB_DIR, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            
            # Re-fetch to update API state
            indicators = fetch_all_live()
            if indicators.get('source') == 'twelvedata.com':
                latest_indicators = indicators
                price = indicators.get('current_price', 0)
                last_full_report = now_aest.strftime('%Y-%m-%d %H:%M:%S AEST')
                last_update = last_full_report
                logger.info(f"[BATCH] === FULL REPORT COMPLETE: ${price:.2f} at {last_full_report} ===")
                return True
            else:
                logger.warning("[BATCH] Report written but follow-up fetch failed")
                last_full_report = now_aest.strftime('%Y-%m-%d %H:%M:%S AEST')
                return True
        else:
            logger.error("[BATCH] Full report generation returned empty/invalid HTML")
            return False
            
    except Exception as e:
        logger.error(f"[BATCH] Full report error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def recalculate_analysis(indicators: dict) -> dict:
    """Recalculate technical levels from live price data."""
    price = indicators.get('current_price', 0)
    high = indicators.get('high', price)
    low = indicators.get('low', price)
    prev = indicators.get('prev_close', price)
    
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
    
    sma_200 = indicators.get('sma_200', 4359)
    indicators['trend_bias'] = 'BULLISH' if price > sma_200 else 'BEARISH'
    indicators['pct_from_ath'] = ((price / 5645.60) - 1) * 100
    
    logger.info(f"[HOURLY] Recalculated: pivot=${pivot:.0f}, trend={indicators['trend_bias']}")
    return indicators


def background_updater():
    """Hourly price updates during market hours."""
    logger.info("[HOURLY] Background updater started (AEST)")
    generate_and_save()
    last_hour = None
    
    while True:
        try:
            now = datetime.now(AEST)
            hour = now.hour
            minute = now.minute
            
            if now.weekday() < 5 and 8 <= hour <= 18:
                if minute == 0 and hour != last_hour:
                    logger.info(f"[HOURLY] Update at {now.strftime('%H:%M')} AEST")
                    generate_and_save()
                    last_hour = hour
            else:
                if minute == 0 and hour != last_hour:
                    logger.info(f"[HOURLY] Off-hours update at {now.strftime('%H:%M')} AEST")
                    generate_and_save()
                    last_hour = hour
            
            time.sleep(60)
        except Exception as e:
            logger.error(f"[HOURLY] Updater error: {e}")
            time.sleep(60)


def start_scheduler():
    """Start APScheduler for 6 AM AEST daily batch report."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        scheduler = BackgroundScheduler(timezone=AEST)
        
        # 6:00 AM AEST, Monday-Friday
        scheduler.add_job(
            generate_full_report_job,
            trigger=CronTrigger(hour=6, minute=0, day_of_week='mon-fri'),
            id='daily_full_report',
            name='XAU/USD Full Daily Report 6AM AEST',
            replace_existing=True,
        )
        
        scheduler.start()
        logger.info("[SCHEDULER] APScheduler started — full report at 6:00 AM AEST Mon-Fri")
        return scheduler
    except ImportError:
        logger.warning("[SCHEDULER] APScheduler not installed — using fallback cron loop")
        # Fallback: manual cron-like check in background thread
        Thread(target=_fallback_scheduler, daemon=True).start()
        return None


def _fallback_scheduler():
    """Fallback scheduler if APScheduler not available."""
    logger.info("[SCHEDULER] Fallback scheduler started — checking for 6:00 AM")
    last_run_date = None
    
    while True:
        try:
            now = datetime.now(AEST)
            
            # 6:00 AM AEST, Mon-Fri, not already run today
            if (now.weekday() < 5 and 
                now.hour == 6 and 
                now.minute == 0 and 
                now.strftime('%Y-%m-%d') != last_run_date):
                
                logger.info(f"[SCHEDULER] Triggering full report at {now.strftime('%H:%M')} AEST")
                generate_full_report_job()
                last_run_date = now.strftime('%Y-%m-%d')
            
            time.sleep(30)
        except Exception as e:
            logger.error(f"[SCHEDULER] Fallback error: {e}")
            time.sleep(60)


# Flask routes
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
        return jsonify({'error': 'Price unavailable', 'source': source, 'last_update': last_update}), 503
    return jsonify({
        'price': latest_indicators.get('current_price'),
        'change': latest_indicators.get('daily_change'),
        'change_pct': latest_indicators.get('daily_change_pct'),
        'source': source,
        'last_update': last_update,
    })

@app.route('/api/status')
def api_status():
    """Health check."""
    from app.twelvedata_fetcher import get_api_key
    key = get_api_key()
    src = latest_indicators.get('source', 'unknown')
    return jsonify({
        'status': 'ok' if src == 'twelvedata.com' else 'error',
        'price': latest_indicators.get('current_price'),
        'source': src,
        'last_update': last_update,
        'last_full_report': last_full_report,
        'api_key_set': bool(key),
        'api_key_preview': key[:8] + '...' if key else 'NOT SET',
    })

@app.route('/trigger-update')
def trigger_update():
    """Force hourly price refresh."""
    success = generate_and_save()
    return jsonify({
        'success': success,
        'price': latest_indicators.get('current_price'),
        'source': latest_indicators.get('source', 'unknown'),
        'last_update': last_update,
    })

@app.route('/trigger-full-report')
def trigger_full_report():
    """Manually trigger the full daily report generation."""
    success = generate_full_report_job()
    return jsonify({
        'success': success,
        'price': latest_indicators.get('current_price'),
        'source': latest_indicators.get('source', 'unknown'),
        'last_full_report': last_full_report,
        'last_update': last_update,
    })


def start():
    """Start server + hourly updater + daily batch scheduler."""
    logger.remove()
    logger.add(sys.stdout, level="INFO", format="<green>{time:HH:mm:ss}</green> | {message}")
    
    # Start hourly price updater
    Thread(target=background_updater, daemon=True).start()
    
    # Start daily 6 AM batch scheduler
    start_scheduler()
    
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Server starting on port {port}")
    logger.info("Routes: / | /api/price | /api/status | /trigger-update | /trigger-full-report")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    start()
