"""Full daily batch report generator for XAU/USD.
Runs at 6 AM AEST every business day — fetches live prices and rewrites complete analysis."""
import os
import sys
from datetime import datetime
from typing import Dict
from loguru import logger
import pytz

AEST = pytz.timezone('Australia/Sydney')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.twelvedata_fetcher import fetch_all_live
from app.report_generator import ReportGenerator


def get_macro_analysis(price: float, dxy: float, ten_year: float) -> Dict[str, str]:
    """Generate dynamic macro analysis based on current price and market conditions."""
    
    # Fed policy section — dynamically adjusted
    if price > 5000:
        fed_tone = "The Fed's hawkish hold at <strong>3.50%-3.75%</strong> is creating headwinds for gold above $5,000. The historic 4-way dissent at April's FOMC signals growing internal pressure to cut."
        fed_bias = "Dovish pivot risk rising — gold supportive if Fed cracks."
    elif price > 4600:
        fed_tone = "The Federal Reserve holds at <strong>3.50%-3.75%</strong> with the most divided committee since 1992 (4 dissents). Markets are pricing 97.4% probability of no change in June, but the trend is toward eventual cuts."
        fed_bias = "Neutral — Fed on hold but bias shifting dovish."
    else:
        fed_tone = "The Federal Reserve holds at <strong>3.50%-3.75%</strong> but incoming Chair Kevin Warsh's 'radical system change' rhetoric is creating policy uncertainty. The April FOMC's 4-way dissent (most divided since 1992) suggests rate cuts are coming sooner than markets expect."
        fed_bias = "Dovish undertone — gold supportive on Fed uncertainty."
    
    # Inflation section
    if ten_year > 4.5:
        infl_tone = f"The 10-year Treasury at <strong>{ten_year:.2f}%</strong> signals elevated inflation expectations. April CPI at 3.8% YoY (3-year high) with Iran conflict adding 0.6-1.1pp to PCE. The gold-real yield correlation has weakened but elevated real yields still cap upside."
    elif ten_year > 4.0:
        infl_tone = f"The 10-year Treasury at <strong>{ten_year:.2f}%</strong> reflects sticky inflation. April CPI at 3.8% YoY beat consensus. Real yields elevated but the correlation with gold has broken down — central bank demand is overriding rate signals."
    else:
        infl_tone = f"The 10-year Treasury at <strong>{ten_year:.2f}%</strong> has eased back, reducing pressure on gold. Inflation remains above target but the trend is moderating — supportive for gold if yields continue lower."
    
    # DXY section
    if dxy > 101:
        dxy_tone = f"DXY at <strong>{dxy:.2f}</strong> is a significant headwind. Above 100.50 is the danger zone for gold — each 1% DXY move = ~$40-60 gold move inversely. Dollar strength driven by safe-haven flows and rate differentials."
    elif dxy > 99:
        dxy_tone = f"DXY at <strong>{dxy:.2f}</strong> sits near critical 100.50 resistance. A sustained break above accelerates gold's correction. Consensus forecasts DXY weakening to 90-96 by Q4 2026 — medium-term gold tailwind."
    else:
        dxy_tone = f"DXY at <strong>{dxy:.2f}</strong> has weakened, providing relief for gold. Below 99.00 is supportive — each 1% DXY drop = ~$40-60 gold upside. The dollar bear case strengthens if Fed cuts materialize."
    
    return {
        'fed': fed_tone,
        'fed_bias': fed_bias,
        'inflation': infl_tone,
        'dxy': dxy_tone,
    }


def get_technical_analysis(price: float, rsi: float, macd: float, adx: float, 
                          sma_200: float, pivot: float, r1: float, s1: float) -> Dict[str, str]:
    """Generate dynamic technical analysis based on live price and indicators."""
    
    # RSI assessment
    if rsi < 30:
        rsi_signal = "OVERSOLD"
        rsi_class = "signal-strong-buy"
        rsi_text = f"RSI at <strong>{rsi:.1f}</strong> is oversold (&lt;30) — bounce potential increasing. However, oversold can stay oversold in strong trends. Wait for bullish divergence or price confirmation before counter-trend longs."
    elif rsi < 40:
        rsi_signal = "SELL"
        rsi_class = "signal-sell"
        rsi_text = f"RSI at <strong>{rsi:.1f}</strong> is bearish but not yet oversold. Room for more downside before a meaningful bounce. Momentum favors shorts."
    elif rsi < 50:
        rsi_signal = "WEAK"
        rsi_class = "signal-neutral"
        rsi_text = f"RSI at <strong>{rsi:.1f}</strong> is neutral-bearish. Below 50 = bearish momentum. Need reclaim of 50+ for bulls to take control."
    elif rsi < 60:
        rsi_signal = "BULLISH"
        rsi_class = "signal-buy"
        rsi_text = f"RSI at <strong>{rsi:.1f}</strong> is bullish. Above 50 = momentum with the bulls. Look for pullbacks to support as long entry opportunities."
    else:
        rsi_signal = "OVERBOUGHT"
        rsi_class = "signal-strong-sell"
        rsi_text = f"RSI at <strong>{rsi:.1f}</strong> is overbought (&gt;70 caution). Profit-taking risk elevated. Consider trimming longs or waiting for pullback to support."
    
    # MACD assessment
    if macd < -20:
        macd_text = f"MACD at <strong>{macd:.2f}</strong> is deeply negative — bearish momentum is accelerating. No bullish crossover in sight. Trend followers should stay short."
    elif macd < 0:
        macd_text = f"MACD at <strong>{macd:.2f}</strong> is negative but improving/worsening. Histogram direction matters — widening = more downside, narrowing = potential bottom forming."
    elif macd < 20:
        macd_text = f"MACD at <strong>{macd:.2f}</strong> is positive but weak. Bullish momentum building but not yet strong. Confirm with price break above resistance."
    else:
        macd_text = f"MACD at <strong>{macd:.2f}</strong> is strongly positive — bullish momentum confirmed. Trend followers long, counter-trend traders stand aside."
    
    # ADX / Trend assessment
    if adx > 40:
        trend_text = f"ADX at <strong>{adx:.1f}</strong> confirms a very strong trend. This is a <strong>trend-following environment</strong> — counter-trend trades are dangerous. Ride the trend until ADX drops below 25."
    elif adx > 25:
        trend_text = f"ADX at <strong>{adx:.1f}</strong> confirms a trending market. Trend-following strategies favored. The trend is your friend until it bends."
    else:
        trend_text = f"ADX at <strong>{adx:.1f}</strong> is below 25 — range-bound environment. Mean-reversion strategies may outperform. Buy support, sell resistance."
    
    # Price vs key levels
    distance_to_sma200 = ((price / sma_200) - 1) * 100
    if price > sma_200 * 1.02:
        price_context = f"Price at <strong>${price:.2f}</strong> is <strong>{distance_to_sma200:.1f}%</strong> above the 200-day SMA (${sma_200:.0f}) — bull market territory. Pullbacks to the 200-SMA are buying opportunities in the broader uptrend."
    elif price > sma_200 * 0.98:
        price_context = f"Price at <strong>${price:.2f}</strong> is testing the 200-day SMA zone (${sma_200:.0f}). This is a <strong>critical juncture</strong> — a decisive break below would flip the long-term bias to bearish."
    else:
        price_context = f"Price at <strong>${price:.2f}</strong> is <strong>{abs(distance_to_sma200):.1f}%</strong> below the 200-day SMA (${sma_200:.0f}) — in correction territory. The longer price stays below, the more likely a deeper correction becomes."
    
    return {
        'rsi_signal': rsi_signal,
        'rsi_class': rsi_class,
        'rsi_text': rsi_text,
        'macd_text': macd_text,
        'adx_text': trend_text,
        'price_context': price_context,
    }


def get_trade_plan(price: float, pivot: float, r1: float, r2: float, r3: float,
                   s1: float, s2: float, s3: float, atr: float, trend_bias: str) -> Dict[str, str]:
    """Generate dynamic trade plan based on current price and levels."""
    
    # Determine scenario based on price vs pivot
    if price > pivot * 1.005:
        scenario = "bullish"
        scenario_title = "BULLISH BIAS"
        scenario_text = f"Price at <strong>${price:.2f}</strong> is above pivot (${pivot:.0f}) — intraday bias is bullish. Look to buy dips toward S1 ${s1:.0f} or play break above R1 ${r1:.0f}."
        long_entry = f"S1 ${s1:.0f} zone on pullback with bullish candlestick"
        long_stop = f"S2 ${s2:.0f}"
        long_tp1 = f"R1 ${r1:.0f}"
        long_tp2 = f"R2 ${r2:.0f}"
        long_tp3 = f"R3 ${r3:.0f}"
        short_entry = f"R2 ${r2:.0f} on rejection with bearish candlestick"
        short_stop = f"R3 ${r3:.0f}"
        short_tp1 = f"R1 ${r1:.0f}"
        short_tp2 = f"Pivot ${pivot:.0f}"
    elif price < pivot * 0.995:
        scenario = "bearish"
        scenario_title = "BEARISH BIAS"
        scenario_text = f"Price at <strong>${price:.2f}</strong> is below pivot (${pivot:.0f}) — intraday bias is bearish. Look to sell rallies toward R1 ${r1:.0f} or play break below S1 ${s1:.0f}."
        long_entry = f"S2 ${s2:.0f} on bullish reversal candlestick"
        long_stop = f"S3 ${s3:.0f}"
        long_tp1 = f"S1 ${s1:.0f}"
        long_tp2 = f"Pivot ${pivot:.0f}"
        long_tp3 = f"R1 ${r1:.0f}"
        short_entry = f"R1 ${r1:.0f} on rejection / Break below S1 ${s1:.0f}"
        short_stop = f"R2 ${r2:.0f}"
        short_tp1 = f"S1 ${s1:.0f}"
        short_tp2 = f"S2 ${s2:.0f}"
    else:
        scenario = "neutral"
        scenario_title = "NEUTRAL / RANGE"
        scenario_text = f"Price at <strong>${price:.2f}</strong> is near pivot (${pivot:.0f}) — no clear bias. Range trade between S1 ${s1:.0f} and R1 ${r1:.0f} until a directional break occurs."
        long_entry = f"S1 ${s1:.0f} with reversal signal"
        long_stop = f"S2 ${s2:.0f}"
        long_tp1 = f"Pivot ${pivot:.0f}"
        long_tp2 = f"R1 ${r1:.0f}"
        long_tp3 = f"R2 ${r2:.0f}"
        short_entry = f"R1 ${r1:.0f} with rejection signal"
        short_stop = f"R2 ${r2:.0f}"
        short_tp1 = f"Pivot ${pivot:.0f}"
        short_tp2 = f"S1 ${s1:.0f}"
    
    return {
        'scenario': scenario,
        'scenario_title': scenario_title,
        'scenario_text': scenario_text,
        'long_entry': long_entry,
        'long_stop': long_stop,
        'long_tp1': long_tp1,
        'long_tp2': long_tp2,
        'long_tp3': long_tp3,
        'short_entry': short_entry,
        'short_stop': short_stop,
        'short_tp1': short_tp1,
        'short_tp2': short_tp2,
        'atr': atr,
    }


def generate_full_report() -> str:
    """Generate the complete daily batch report with fresh prices and rewritten analysis."""
    logger.info("=== STARTING FULL BATCH REPORT ===")
    
    now_aest = datetime.now(AEST)
    logger.info(f"Batch time: {now_aest.strftime('%Y-%m-%d %H:%M')} AEST")
    
    # Step 1: Fetch live data
    indicators = fetch_all_live()
    source = indicators.get('source', 'unknown')
    price = indicators.get('current_price', 0)
    
    if source != 'twelvedata.com':
        logger.error("Cannot generate full report — no live data")
        return ""
    
    logger.info(f"Live price: ${price:.2f}")
    
    # Step 2: Recalculate levels from live price
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
    
    # Step 3: Generate dynamic analysis sections
    rsi = indicators.get('rsi', 35.42)
    macd = indicators.get('macd', -26.31)
    adx = indicators.get('adx', 46.6)
    dxy = indicators.get('dxy', 99.27)
    ten_year = indicators.get('ten_year', 4.46)
    
    macro = get_macro_analysis(price, dxy, ten_year)
    technical = get_technical_analysis(price, rsi, macd, adx, sma_200, pivot, indicators['r1'], indicators['s1'])
    trade = get_trade_plan(price, pivot, indicators['r1'], indicators['r2'], indicators['r3'],
                          indicators['s1'], indicators['s2'], indicators['s3'], atr, indicators['trend_bias'])
    
    # Step 4: Build the full HTML report
    html = build_full_html(indicators, macro, technical, trade, now_aest)
    
    logger.info(f"=== FULL REPORT COMPLETE: ${price:.2f} ===")
    return html


def build_full_html(indicators: Dict, macro: Dict, technical: Dict, trade: Dict, now_aest: datetime) -> str:
    """Build the complete HTML report with all dynamic sections."""
    
    price = indicators['current_price']
    change = indicators['daily_change']
    change_pct = indicators['daily_change_pct']
    dxy = indicators['dxy']
    dxy_change = indicators.get('dxy_change', 0)
    ten_year = indicators['ten_year']
    vix = indicators.get('vix', 18.5)
    usd_jpy = indicators.get('usd_jpy', 159.0)
    oil = indicators.get('oil', 103.67)
    rsi = indicators.get('rsi', 35.42)
    macd = indicators.get('macd', -26.31)
    adx = indicators.get('adx', 46.6)
    sma_200 = indicators.get('sma_200', 4359)
    ath = 5645.60
    pct_from_ath = indicators.get('pct_from_ath', -19.6)
    trend_bias = indicators.get('trend_bias', 'BEARISH')
    
    # Signal
    if rsi < 30 and macd < 0:
        signal, signal_class = "STRONG SELL", "signal-strong-sell"
    elif rsi < 45 and macd < 0:
        signal, signal_class = "SELL", "signal-sell"
    elif rsi > 70 and macd > 0:
        signal, signal_class = "STRONG BUY", "signal-strong-buy"
    elif rsi > 55 and macd > 0:
        signal, signal_class = "BUY", "signal-buy"
    else:
        signal, signal_class = "NEUTRAL", "signal-neutral"
    
    bias = "BEARISH" if trend_bias == 'BEARISH' else "BULLISH" if trend_bias == 'BULLISH' else "NEUTRAL"
    
    # Executive summary based on price
    if price < 4400:
        exec_summary = f"<strong>Primary Bias: {bias}</strong> — Gold has broken below critical $4,400 support and is testing the 200-day SMA zone ($4,359). A sustained break below $4,350 opens the door to $4,200-$4,100. Extreme positioning (86% retail long) creates cascading risk. Only counter-trend longs at 200-SMA with tight stops."
    elif price < 4600:
        exec_summary = f"<strong>Primary Bias: {bias}</strong> — Gold is consolidating in the $4,400-$4,600 range. The 200-day SMA at $4,359 is the line in the sand for the bull market. Below = deeper correction to $4,200; above = recovery toward $4,750. Key catalyst: Fed policy trajectory and DXY direction."
    elif price < 4800:
        exec_summary = f"<strong>Primary Bias: {bias}</strong> — Gold is recovering off the 200-SMA support. Needs a break above $4,800 to confirm the correction is over. DXY direction and Fed communication are the key drivers. Accumulation zone for long-term holders."
    else:
        exec_summary = f"<strong>Primary Bias: {bias}</strong> — Gold is back in the $4,800+ zone, challenging resistance. A break above $4,900 targets $5,000+. DXY weakness and Fed dovishness are the primary tailwinds."
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="3600">
<title>XAU/USD Daily Report - {now_aest.strftime('%A, %B %d, %Y')}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; color: #333; line-height: 1.6; }}
.container {{ max-width: 800px; margin: 0 auto; background: #fff; }}
.header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; padding: 30px; text-align: center; }}
.header h1 {{ font-size: 28px; margin-bottom: 8px; color: #daa520; }}
.header .date {{ font-size: 14px; color: #888; }}
.batch-badge {{ display: inline-block; background: #daa520; color: #1a1a2e; padding: 4px 12px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-top: 8px; }}
.price-bar {{ display: flex; justify-content: center; align-items: center; gap: 30px; padding: 20px; background: #0f3460; color: #fff; }}
.price-main {{ text-align: center; }}
.price-label {{ font-size: 12px; text-transform: uppercase; color: #888; }}
.price-value {{ font-size: 36px; font-weight: bold; color: #daa520; }}
.price-change {{ font-size: 16px; }}
.bullish {{ color: #22c55e; }} .bearish {{ color: #ef4444; }} .neutral {{ color: #eab308; }}
.section {{ padding: 25px 30px; border-bottom: 1px solid #eee; }}
.section h2 {{ font-size: 20px; color: #1a1a2e; margin-bottom: 15px; border-left: 4px solid #daa520; padding-left: 12px; }}
.section h3 {{ font-size: 16px; color: #333; margin: 15px 0 10px; }}
.section p {{ margin-bottom: 12px; font-size: 14px; }}
table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 13px; }}
th {{ background: #1a1a2e; color: #daa520; padding: 10px 12px; text-align: left; font-weight: 600; }}
td {{ padding: 10px 12px; border-bottom: 1px solid #eee; }}
tr:nth-child(even) {{ background: #f8f9fa; }}
.level-box {{ display: inline-block; padding: 3px 10px; border-radius: 4px; font-weight: bold; font-size: 13px; }}
.level-r {{ background: #fee; color: #c00; }} .level-s {{ background: #efe; color: #080; }} .level-p {{ background: #eef; color: #00c; }}
.signal-box {{ display: inline-block; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 14px; }}
.signal-strong-sell {{ background: #fee; color: #c00; }} .signal-sell {{ background: #ffe0e0; color: #d00; }}
.signal-buy {{ background: #efe; color: #080; }} .signal-strong-buy {{ background: #dfd; color: #060; }}
.signal-neutral {{ background: #ffe; color: #880; }}
.highlight {{ background: #fff8e1; padding: 15px; border-left: 4px solid #daa520; margin: 15px 0; }}
.warning {{ background: #fee; padding: 15px; border-left: 4px solid #c00; margin: 15px 0; }}
.info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }}
.info-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; }}
.info-card .label {{ font-size: 11px; text-transform: uppercase; color: #888; margin-bottom: 5px; }}
.info-card .value {{ font-size: 18px; font-weight: bold; color: #1a1a2e; }}
.trade-box {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: #fff; padding: 20px; border-radius: 8px; margin: 15px 0; }}
.trade-box h4 {{ color: #daa520; margin-bottom: 10px; font-size: 16px; }}
.trade-row {{ display: flex; justify-content: space-between; margin: 8px 0; font-size: 14px; }}
.trade-label {{ color: #888; }} .trade-value {{ font-weight: bold; }}
.scenario {{ padding: 12px 15px; border-radius: 6px; margin: 10px 0; }}
.scenario-bearish {{ background: #fee; border-left: 4px solid #c00; }}
.scenario-bullish {{ background: #efe; border-left: 4px solid #080; }}
.scenario-neutral {{ background: #f0f0f0; border-left: 4px solid #888; }}
.scenario-title {{ font-weight: bold; margin-bottom: 5px; }}
.footer {{ background: #1a1a2e; color: #888; padding: 20px; text-align: center; font-size: 12px; }}
ul {{ margin-left: 20px; margin-bottom: 12px; }} li {{ margin-bottom: 6px; font-size: 14px; }}
</style></head>
<body>
<div class="container">

<!-- Header -->
<div class="header">
    <h1>XAU/USD Daily Trading Report</h1>
    <div class="date">{now_aest.strftime('%A, %B %d, %Y')} | Prepared for Gorjan Ivanovski</div>
    <div class="batch-badge">FULL DAILY REPORT — 6:00 AM AEST</div>
</div>

<!-- Price Bar -->
<div class="price-bar">
    <div class="price-main">
        <div class="price-label">XAU/USD</div>
        <div class="price-value {'bullish' if change >= 0 else 'bearish'}">${price:.2f}</div>
        <div class="price-change {'bullish' if change >= 0 else 'bearish'}">
            {'+' if change >= 0 else ''}{change:.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)
        </div>
        <div style="font-size: 11px; color: #888; margin-top: 4px;">
            Updated: {now_aest.strftime('%a %d %b %H:%M')} AEST | Source: twelvedata.com
        </div>
    </div>
    <div class="price-main">
        <div class="price-label">From ATH</div>
        <div class="price-value {'bearish' if pct_from_ath < 0 else 'bullish'}">{pct_from_ath:.1f}%</div>
        <div class="price-change">ATH: ${ath:.0f}</div>
    </div>
    <div class="price-main">
        <div class="price-label">Signal</div>
        <div><span class="signal-box {signal_class}">{signal}</span></div>
        <div class="price-change">RSI: {rsi:.1f} | ADX: {adx:.1f}</div>
    </div>
</div>

<!-- Executive Summary -->
<div class="section">
    <h2>Executive Summary</h2>
    <div class="warning">
        {exec_summary}
    </div>
    <div class="info-grid">
        <div class="info-card"><div class="label">Fed Funds Rate</div><div class="value">3.50%-3.75%</div></div>
        <div class="info-card"><div class="label">DXY</div><div class="value">{dxy:.2f} <span class="{'bullish' if dxy_change >= 0 else 'bearish'}">({dxy_change:+.2f}%)</span></div></div>
        <div class="info-card"><div class="label">10Y Treasury</div><div class="value">{ten_year:.2f}%</div></div>
        <div class="info-card"><div class="label">VIX</div><div class="value">{vix:.1f}</div></div>
        <div class="info-card"><div class="label">USD/JPY</div><div class="value">{usd_jpy:.2f}</div></div>
        <div class="info-card"><div class="label">Oil (WTI)</div><div class="value">${oil:.2f}</div></div>
    </div>
</div>

<!-- Macro Analysis -->
<div class="section">
    <h2>Macro Analysis</h2>
    <h3>Federal Reserve Policy</h3>
    <p>{macro['fed']}</p>
    <div class="highlight"><strong>Bias:</strong> {macro['fed_bias']}</div>
    
    <h3>Inflation & Real Yields</h3>
    <p>{macro['inflation']}</p>
    
    <h3>US Dollar</h3>
    <p>{macro['dxy']}</p>
</div>

<!-- Technical Analysis -->
<div class="section">
    <h2>Technical Analysis</h2>
    <h3>Price Context</h3>
    <p>{technical['price_context']}</p>
    
    <h3>Momentum Indicators</h3>
    <table>
        <tr><th>Indicator</th><th>Value</th><th>Signal</th><th>Assessment</th></tr>
        <tr><td>RSI (14)</td><td>{rsi:.1f}</td><td><span class="signal-box {technical['rsi_class']}">{technical['rsi_signal']}</span></td><td>{technical['rsi_text']}</td></tr>
        <tr><td>MACD</td><td>{macd:.2f}</td><td><span class="signal-box {'signal-strong-sell' if macd < 0 else 'signal-buy'}">{'SELL' if macd < 0 else 'BUY'}</span></td><td>{technical['macd_text']}</td></tr>
        <tr><td>ADX (14)</td><td>{adx:.1f}</td><td><span class="signal-box signal-neutral">{'STRONG TREND' if adx > 40 else 'TRENDING' if adx > 25 else 'RANGE'}</span></td><td>{technical['adx_text']}</td></tr>
    </table>

    <h3>Key Levels (Recalculated from Live Data)</h3>
    <table>
        <tr><th>Type</th><th>Level</th><th>Price</th><th>Significance</th></tr>
        <tr><td>Resistance</td><td><span class="level-box level-r">R3</span></td><td>${indicators['r3']:.0f}</td><td>Extended target / channel resistance</td></tr>
        <tr><td>Resistance</td><td><span class="level-box level-r">R2</span></td><td>${indicators['r2']:.0f}</td><td>Strong resistance / take profit</td></tr>
        <tr><td>Resistance</td><td><span class="level-box level-r">R1</span></td><td>${indicators['r1']:.0f}</td><td>First resistance / short entry</td></tr>
        <tr><td>Pivot</td><td><span class="level-box level-p">P</span></td><td>${indicators['pivot']:.0f}</td><td>Session bias divider</td></tr>
        <tr><td>Support</td><td><span class="level-box level-s">S1</span></td><td>${indicators['s1']:.0f}</td><td>First support / long entry</td></tr>
        <tr><td>Support</td><td><span class="level-box level-s">S2</span></td><td>${indicators['s2']:.0f}</td><td>Strong support / add to longs</td></tr>
        <tr><td>Support</td><td><span class="level-box level-s">S3</span></td><td>${indicators['s3']:.0f}</td><td>Last defence / stop for longs</td></tr>
        <tr><td>Support</td><td><span class="level-box level-s">200-SMA</span></td><td>${sma_200:.0f}</td><td>Bull market line</td></tr>
    </table>
</div>

<!-- Trade Plan -->
<div class="section">
    <h2>Trade Plan & Strategy</h2>
    
    <div class="scenario scenario-{trade['scenario']}">
        <div class="scenario-title">{trade['scenario_title']}</div>
        {trade['scenario_text']}
    </div>
    
    <div class="trade-box">
        <h4>LONG SETUP</h4>
        <div class="trade-row"><span class="trade-label">Entry:</span><span class="trade-value">{trade['long_entry']}</span></div>
        <div class="trade-row"><span class="trade-label">Stop Loss:</span><span class="trade-value" style="color:#ef4444">{trade['long_stop']}</span></div>
        <div class="trade-row"><span class="trade-label">TP1:</span><span class="trade-value" style="color:#22c55e">{trade['long_tp1']}</span></div>
        <div class="trade-row"><span class="trade-label">TP2:</span><span class="trade-value" style="color:#22c55e">{trade['long_tp2']}</span></div>
        <div class="trade-row"><span class="trade-label">TP3:</span><span class="trade-value" style="color:#22c55e">{trade['long_tp3']}</span></div>
    </div>
    
    <div class="trade-box">
        <h4>SHORT SETUP</h4>
        <div class="trade-row"><span class="trade-label">Entry:</span><span class="trade-value">{trade['short_entry']}</span></div>
        <div class="trade-row"><span class="trade-label">Stop Loss:</span><span class="trade-value" style="color:#ef4444">{trade['short_stop']}</span></div>
        <div class="trade-row"><span class="trade-label">TP1:</span><span class="trade-value" style="color:#22c55e">{trade['short_tp1']}</span></div>
        <div class="trade-row"><span class="trade-label">TP2:</span><span class="trade-value" style="color:#22c55e">{trade['short_tp2']}</span></div>
    </div>
    
    <div class="trade-box">
        <h4>Risk Management</h4>
        <div class="trade-row"><span class="trade-label">Position Size:</span><span class="trade-value">Risk 1-2% max per trade</span></div>
        <div class="trade-row"><span class="trade-label">ATR (today):</span><span class="trade-value">${trade['atr']:.0f}</span></div>
        <div class="trade-row"><span class="trade-label">Leverage:</span><span class="trade-value">Max 5:1 on intraday</span></div>
        <div class="trade-row"><span class="trade-label">Best Session:</span><span class="trade-value">London-NY overlap (8-11 PM AEST)</span></div>
        <div class="trade-row"><span class="trade-label">Avoid:</span><span class="trade-value">Holdings through FOMC, CPI, NFP</span></div>
    </div>
</div>

<!-- Footer -->
<div class="footer">
    <p>XAU/USD Daily Reporter | Full Daily Report generated at {now_aest.strftime('%a %d %b %H:%M')} AEST | Source: twelvedata.com</p>
    <p>Next full report: Tomorrow 6:00 AM AEST | Hourly price updates during market hours</p>
</div>

</div></body></html>"""
    
    return html
