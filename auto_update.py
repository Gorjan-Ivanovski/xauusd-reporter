#!/usr/bin/env python3
"""Auto-updater for XAU/USD Dashboard. Fetches live prices hourly, redeploys site."""
import os, sys, time, subprocess
from datetime import datetime
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.goldapi_fetcher import fetch_all_live
from app.report_generator import ReportGenerator

WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'updater.log')

def log(msg):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"{ts} | {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def fetch_and_build():
    """Fetch live data, generate HTML, save to web dir."""
    log("Fetching live data from GoldAPI...")
    indicators = fetch_all_live()
    price = indicators.get('current_price', 0)
    source = indicators.get('source', 'goldapi.io')
    log(f"Live price: ${price:.2f} ({source})")
    
    generator = ReportGenerator()
    html = generator.generate(indicators, {})
    
    now = datetime.now()
    html = html.replace('Saturday, May 16, 2026', now.strftime('%A, %B %d, %Y'))
    
    os.makedirs(WEB_DIR, exist_ok=True)
    index_path = os.path.join(WEB_DIR, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    log(f"Report built: {index_path}")
    return True

def redeploy():
    """Redeploy the static site using deploy_website tool."""
    try:
        log("Redeploying site...")
        # Use subprocess to call the deployment
        result = subprocess.run(
            ['python3', '-c', 
             'import json, urllib.request; '
             'req = urllib.request.Request("http://localhost:8080/deploy", '
             'data=json.dumps({"type":"static","local_dir":"/mnt/agents/output/xauusd-reporter/web","description":"XAU/USD Live"}).encode(), '
             'headers={"Content-Type":"application/json"}); '
             'urllib.request.urlopen(req, timeout=30)'],
            capture_output=True, timeout=35
        )
        log("Redeploy signal sent")
        return True
    except Exception as e:
        log(f"Redeploy hook skipped: {e}")
        return False

def main():
    log("=" * 50)
    log("XAU/USD Auto-Updater Starting")
    log("=" * 50)
    
    # Initial build
    fetch_and_build()
    
    last_update_hour = None
    last_deploy_hour = None
    
    try:
        while True:
            now = datetime.now()
            hour = now.hour
            minute = now.minute
            
            # Hourly update during market hours (Mon-Fri 8-18)
            if now.weekday() < 5 and 8 <= hour <= 18 and minute == 0 and last_update_hour != hour:
                log(f"=== HOURLY UPDATE {hour}:00 ===")
                fetch_and_build()
                last_update_hour = hour
            
            # Redeploy every hour (top of hour) regardless of data update
            # This catches manual updates too
            if minute == 0 and last_deploy_hour != hour:
                log(f"=== REDEPLOY {hour}:00 ===")
                # Can't directly call deploy_website from subprocess, 
                # so we write a flag that the orchestrator can check
                flag_path = os.path.join(WEB_DIR, '.redeploy')
                with open(flag_path, 'w') as f:
                    f.write(now.isoformat())
                last_deploy_hour = hour
            
            # Check for forced redeploy every 5 minutes
            if minute % 5 == 0 and minute != 0:
                # Always rebuild to keep timestamps fresh
                pass  # Skip to avoid excessive API calls
            
            time.sleep(30)
    except KeyboardInterrupt:
        log("Stopped")

if __name__ == '__main__':
    main()
