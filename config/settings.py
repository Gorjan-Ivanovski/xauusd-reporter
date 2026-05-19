"""Configuration settings for XAU/USD Daily Reporter."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Base paths
BASE_DIR = Path(__file__).parent.parent
APP_DIR = BASE_DIR / 'app'
LOG_DIR = BASE_DIR / 'logs'

# Email settings
# TwelveData API (free tier: 800 calls/day)
# Sign up: https://twelvedata.com/pricing
TWELVEDATA_API_KEY = os.getenv('TWELVEDATA_API_KEY', '')

# Email provider priority: SendGrid > SMTP
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')

# Fallback SMTP settings
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')

# Recipient
RECIPIENT_EMAIL = os.getenv('RECIPIENT_EMAIL', 'Gorjan.ivanovski@gmail.com')

# Scheduling
REPORT_TIME = os.getenv('REPORT_TIME', '07:00')  # 24-hour format
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Skopje')

# Trading symbols
SYMBOLS = {
    'gold': 'GC=F',           # Gold futures
    'gold_etf': 'GLD',        # SPDR Gold ETF
    'dxy': 'DX-Y.NYB',       # Dollar Index
    'ten_year': '^TNX',       # 10-Year Treasury yield
    'two_year': '^IRX',       # 2-Year Treasury yield
    'vix': '^VIX',            # Volatility Index
    'spy': 'SPY',             # S&P 500 ETF
    'usd_jpy': 'USDJPY=X',    # USD/JPY
    'eur_usd': 'EURUSD=X',    # EUR/USD
    'oil': 'CL=F',            # Crude Oil
    'silver': 'SI=F',         # Silver
}

# Report template colors
COLORS = {
    'bullish': '#22c55e',
    'bearish': '#ef4444',
    'neutral': '#eab308',
    'primary': '#b8860b',
    'secondary': '#daa520',
    'bg_dark': '#1a1a2e',
    'bg_card': '#16213e',
    'text': '#e0e0e0',
    'text_muted': '#888888',
    'border': '#2a2a4a',
}

# Working days (Monday=0, Sunday=6)
WORKING_DAYS = [0, 1, 2, 3, 4]  # Monday through Friday

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 60  # seconds
