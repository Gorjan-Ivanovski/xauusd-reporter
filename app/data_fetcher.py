"""Market data fetcher for XAU/USD daily report."""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger
import time

from config.settings import SYMBOLS


class MarketDataFetcher:
    """Fetches market data for gold trading analysis."""

    def __init__(self):
        self.data = {}
        self.indicators = {}

    def fetch_all(self) -> Dict:
        """Fetch all required market data."""
        logger.info("Fetching market data...")

        # Gold data (primary)
        self.data['gold'] = self._fetch_ticker(SYMBOLS['gold'], period='3mo', interval='1d')
        self.data['gold_1h'] = self._fetch_ticker(SYMBOLS['gold'], period='5d', interval='1h')

        # USD Index
        self.data['dxy'] = self._fetch_ticker(SYMBOLS['dxy'], period='3mo', interval='1d')

        # Treasury yields
        self.data['ten_year'] = self._fetch_ticker(SYMBOLS['ten_year'], period='3mo', interval='1d')
        self.data['two_year'] = self._fetch_ticker(SYMBOLS['two_year'], period='3mo', interval='1d')

        # Volatility & equity
        self.data['vix'] = self._fetch_ticker(SYMBOLS['vix'], period='1mo', interval='1d')
        self.data['spy'] = self._fetch_ticker(SYMBOLS['spy'], period='3mo', interval='1d')

        # FX pairs
        self.data['usd_jpy'] = self._fetch_ticker(SYMBOLS['usd_jpy'], period='3mo', interval='1d')
        self.data['eur_usd'] = self._fetch_ticker(SYMBOLS['eur_usd'], period='3mo', interval='1d')

        # Commodities
        self.data['oil'] = self._fetch_ticker(SYMBOLS['oil'], period='3mo', interval='1d')
        self.data['silver'] = self._fetch_ticker(SYMBOLS['silver'], period='3mo', interval='1d')

        # Gold ETF
        self.data['gold_etf'] = self._fetch_ticker(SYMBOLS['gold_etf'], period='3mo', interval='1d')

        self._calculate_indicators()
        return self.data, self.indicators

    def _fetch_ticker(self, symbol: str, period: str, interval: str) -> Optional[pd.DataFrame]:
        """Fetch data for a single ticker with retry logic."""
        for attempt in range(3):
            try:
                ticker = yf.Ticker(symbol)
                df = ticker.history(period=period, interval=interval)
                if df.empty:
                    logger.warning(f"Empty data for {symbol}")
                    return None
                return df
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {symbol}: {e}")
                time.sleep(2)
        logger.error(f"Failed to fetch {symbol} after 3 attempts")
        return None

    def _calculate_indicators(self):
        """Calculate technical indicators from price data."""
        gold = self.data.get('gold')
        if gold is None or gold.empty:
            logger.warning("No gold data to calculate indicators")
            return

        close = gold['Close']
        high = gold['High']
        low = gold['Low']

        # Current price and changes
        self.indicators['current_price'] = close.iloc[-1]
        self.indicators['prev_close'] = close.iloc[-2] if len(close) > 1 else close.iloc[-1]
        self.indicators['daily_change'] = close.iloc[-1] - close.iloc[-2] if len(close) > 1 else 0
        self.indicators['daily_change_pct'] = (close.iloc[-1] / close.iloc[-2] - 1) * 100 if len(close) > 1 else 0

        # ATH and distance
        self.indicators['ath'] = high.max()
        self.indicators['ath_date'] = high.idxmax().strftime('%Y-%m-%d')
        self.indicators['pct_from_ath'] = (close.iloc[-1] / self.indicators['ath'] - 1) * 100

        # Moving averages
        self.indicators['sma_20'] = close.rolling(20).mean().iloc[-1]
        self.indicators['sma_50'] = close.rolling(50).mean().iloc[-1]
        self.indicators['sma_100'] = close.rolling(100).mean().iloc[-1]
        self.indicators['sma_200'] = close.rolling(200).mean().iloc[-1]

        # RSI
        self.indicators['rsi'] = self._calculate_rsi(close, 14)

        # MACD
        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()
        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        self.indicators['macd'] = macd_line.iloc[-1]
        self.indicators['macd_signal'] = signal_line.iloc[-1]
        self.indicators['macd_hist'] = macd_line.iloc[-1] - signal_line.iloc[-1]

        # ATR
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        self.indicators['atr_14'] = tr.rolling(14).mean().iloc[-1]

        # Bollinger Bands
        sma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        self.indicators['bb_upper'] = (sma_20 + 2 * std_20).iloc[-1]
        self.indicators['bb_lower'] = (sma_20 - 2 * std_20).iloc[-1]
        self.indicators['bb_pct'] = (close.iloc[-1] - self.indicators['bb_lower']) / (self.indicators['bb_upper'] - self.indicators['bb_lower'])

        # Pivot points (classic)
        prev_high = high.iloc[-2] if len(high) > 1 else high.iloc[-1]
        prev_low = low.iloc[-2] if len(low) > 1 else low.iloc[-1]
        prev_close = close.iloc[-2] if len(close) > 1 else close.iloc[-1]
        pivot = (prev_high + prev_low + prev_close) / 3
        self.indicators['pivot'] = pivot
        self.indicators['r1'] = 2 * pivot - prev_low
        self.indicators['r2'] = pivot + (prev_high - prev_low)
        self.indicators['r3'] = pivot + 2 * (prev_high - prev_low)
        self.indicators['s1'] = 2 * pivot - prev_high
        self.indicators['s2'] = pivot - (prev_high - prev_low)
        self.indicators['s3'] = pivot - 2 * (prev_high - prev_low)

        # 52-week range
        self.indicators['low_52w'] = low.min()
        self.indicators['high_52w'] = high.max()
        self.indicators['pct_52w'] = (close.iloc[-1] - low.min()) / (high.max() - low.min()) * 100

        # DXY data
        dxy = self.data.get('dxy')
        if dxy is not None and not dxy.empty:
            self.indicators['dxy'] = dxy['Close'].iloc[-1]
            self.indicators['dxy_change'] = (dxy['Close'].iloc[-1] / dxy['Close'].iloc[-2] - 1) * 100 if len(dxy) > 1 else 0

        # Yield data
        tnx = self.data.get('ten_year')
        if tnx is not None and not tnx.empty:
            self.indicators['ten_year'] = tnx['Close'].iloc[-1]

        irx = self.data.get('two_year')
        if irx is not None and not irx.empty:
            self.indicators['two_year'] = irx['Close'].iloc[-1]

        # VIX
        vix = self.data.get('vix')
        if vix is not None and not vix.empty:
            self.indicators['vix'] = vix['Close'].iloc[-1]

        # USD/JPY
        usdjpy = self.data.get('usd_jpy')
        if usdjpy is not None and not usdjpy.empty:
            self.indicators['usd_jpy'] = usdjpy['Close'].iloc[-1]

        # Oil
        oil = self.data.get('oil')
        if oil is not None and not oil.empty:
            self.indicators['oil'] = oil['Close'].iloc[-1]

        # Silver
        silver = self.data.get('silver')
        if silver is not None and not silver.empty:
            self.indicators['silver'] = silver['Close'].iloc[-1]
            self.indicators['gold_silver_ratio'] = close.iloc[-1] / silver['Close'].iloc[-1]

        # ETF flows
        etf = self.data.get('gold_etf')
        if etf is not None and not etf.empty:
            self.indicators['gld_price'] = etf['Close'].iloc[-1]

        logger.info(f"Indicators calculated. Gold: ${self.indicators['current_price']:.2f}, RSI: {self.indicators['rsi']:.1f}")

    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI."""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1]

    def get_support_resistance(self) -> Dict:
        """Calculate key support and resistance levels."""
        gold = self.data.get('gold')
        if gold is None:
            return {}

        close = gold['Close']
        recent = close.tail(30)

        # Recent swing highs/lows
        highs = recent.nlargest(5).sort_values(ascending=False).tolist()
        lows = recent.nsmallest(5).sort_values(ascending=True).tolist()

        return {
            'resistance': highs,
            'support': lows,
            'sma_20': self.indicators.get('sma_20'),
            'sma_50': self.indicators.get('sma_50'),
            'sma_100': self.indicators.get('sma_100'),
            'sma_200': self.indicators.get('sma_200'),
            'r1': self.indicators.get('r1'),
            'r2': self.indicators.get('r2'),
            's1': self.indicators.get('s1'),
            's2': self.indicators.get('s2'),
            'pivot': self.indicators.get('pivot'),
        }
