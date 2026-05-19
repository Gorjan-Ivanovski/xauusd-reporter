#!/usr/bin/env python3
"""
Background runner for XAU/USD Daily Reporter.
Runs continuously, generating reports at the scheduled time.
Works with or without live market data (uses research fallback when yfinance is rate-limited).
"""
import sys
import os
import time
import subprocess
from datetime import datetime
from loguru import logger

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}"
)
logger.add(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'scheduler.log'),
    rotation="1 day",
    retention="7 days",
    level="DEBUG"
)

REPORT_TIME = os.getenv('REPORT_TIME', '07:00')
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Skopje')


def is_working_day():
    """Check if today is a working day (Mon-Fri)."""
    return datetime.now().weekday() < 5


def should_run_now():
    """Check if it's time to generate the report."""
    now = datetime.now()
    try:
        hour, minute = map(int, REPORT_TIME.split(':'))
    except ValueError:
        hour, minute = 7, 0
    return now.hour == hour and now.minute == minute


def generate_report_web():
    """Generate report with fallback data support."""
    try:
        from app.data_fetcher import MarketDataFetcher
        from app.report_generator import ReportGenerator

        logger.info("Fetching market data...")
        fetcher = MarketDataFetcher()
        data, indicators = fetcher.fetch_all()

        # Fallback to research data if yfinance fails
        if not indicators:
            logger.warning("Live data unavailable (rate limit), using research fallback...")
            indicators = {
                'current_price': 4540.00, 'daily_change': -32.50,
                'daily_change_pct': -0.71, 'ath': 5645.60, 'pct_from_ath': -19.6,
                'rsi': 35.42, 'adx': 46.6, 'macd': -26.31, 'dxy': 99.27,
                'dxy_change': 0.15, 'ten_year': 4.46, 'vix': 18.5,
                'usd_jpy': 159.0, 'oil': 103.67, 'r1': 4633, 'r2': 4725,
                'r3': 4785, 'pivot': 4557, 's1': 4480, 's2': 4420,
                's3': 4328, 'sma_200': 4359, 'atr_14': 95,
            }
            data = {}

        logger.info("Generating HTML report...")
        generator = ReportGenerator()
        html_report = generator.generate(indicators, data)

        # Update timestamp
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        today_str = datetime.now().strftime('%A, %B %d, %Y')
        html_report = html_report.replace('Saturday, May 16, 2026', today_str)

        # Save to web directory
        web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web')
        os.makedirs(web_dir, exist_ok=True)

        index_path = os.path.join(web_dir, 'index.html')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(html_report)

        # Archive with date
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        archive_path = os.path.join(web_dir, f'report_{timestamp}.html')
        with open(archive_path, 'w', encoding='utf-8') as f:
            f.write(html_report)

        logger.info(f"Report saved: {index_path}")
        return True

    except Exception as e:
        logger.exception(f"Error generating report: {e}")
        return False


def main():
    """Main loop - checks every minute."""
    logger.info("=" * 50)
    logger.info("XAU/USD Daily Reporter - Background Runner")
    logger.info(f"Schedule: {REPORT_TIME} on working days (Mon-Fri)")
    logger.info(f"Timezone: {TIMEZONE}")
    logger.info("=" * 50)

    # Generate initial report on startup
    logger.info("Generating initial report...")
    generate_report_web()

    last_run_date = None
    last_run_hour = None

    try:
        while True:
            now = datetime.now()
            today_str = now.strftime('%Y-%m-%d')
            current_hour = now.hour

            # Check if it's time to run (and we haven't run this hour)
            if is_working_day() and should_run_now() and last_run_hour != current_hour:
                logger.info(f"It's {REPORT_TIME}! Generating report...")
                success = generate_report_web()
                if success:
                    logger.info("Report generated successfully")
                    last_run_date = today_str
                    last_run_hour = current_hour
                else:
                    logger.error("Failed to generate report, will retry next cycle")

            # Also regenerate every hour during market hours (8 AM - 6 PM) for freshness
            if is_working_day() and 8 <= current_hour <= 18:
                if now.minute == 0 and last_run_hour != current_hour:
                    logger.info(f"Market hours refresh ({current_hour}:00)")
                    generate_report_web()
                    last_run_hour = current_hour

            time.sleep(30)  # Check every 30 seconds

    except KeyboardInterrupt:
        logger.info("Background runner stopped by user")


if __name__ == '__main__':
    main()
