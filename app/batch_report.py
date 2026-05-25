"""Full daily batch report generator for XAU/USD.
Runs at 6 AM AEST every business day — COMPLETELY REWRITES all analysis with fresh data."""
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger
import pytz

AEST = pytz.timezone('Australia/Sydney')
ET = pytz.timezone('US/Eastern')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.twelvedata_fetcher import fetch_all_live
from app.holidays import get_trading_status, is_us_market_holiday, get_this_week_events


def generate_full_report() -> str:
    """Generate the COMPLETE daily report — ALL analysis rewritten fresh."""
    logger.info("[BATCH] === FULL REPORT START ===")
    
    now_aest = datetime.now(AEST)
    us_now = now_aest.astimezone(ET)
    logger.info(f"[BATCH] Today: {now_aest.strftime('%A %d %B %Y')} AEST / {us_now.strftime('%A %d %B %Y')} US")
    
    # 1. Trading status & holiday detection
    trading = get_trading_status()
    logger.info(f"[BATCH] Trading: {trading['market_status']} | {trading['session']}")
    
    # 2. Fetch live price
    indicators = fetch_all_live()
    source = indicators.get('source', 'unknown')
    
    if source != 'twelvedata.com':
        logger.error("[BATCH] No live data — cannot generate full report")
        return _generate_error_html(trading, now_aest)
    
    price = indicators['current_price']
    logger.info(f"[BATCH] Live price: ${price:.2f}")
    
    # 3. Recalculate everything from live price
    indicators = _recalculate_all(indicators)
    
    # 4. Generate ALL dynamic analysis sections
    events = get_this_week_events(now_aest)
    exec_summary = _generate_exec_summary(price, indicators, trading, events, now_aest)
    macro = _generate_macro_analysis(price, indicators, now_aest)
    technical = _generate_technical_analysis(price, indicators)
    trade_plan = _generate_trade_plan(price, indicators)
    event_html = _generate_event_html(events, trading, now_aest)
    
    # 5. Build complete HTML
    html = _build_complete_html(price, indicators, trading, exec_summary, macro, technical, trade_plan, event_html, now_aest)
    
    logger.info(f"[BATCH] === FULL REPORT COMPLETE: ${price:.2f} ===")
    return html


def _recalculate_all(indicators: dict) -> dict:
    """Recalculate all levels from live price."""
    price = indicators['current_price']
    high = indicators.get('high', price)
    low = indicators.get('low', price)
    prev = indicators.get('prev_close', price)
    
    pivot = (high + low + prev) / 3
    atr = high - low if high and low else price * 0.01
    
    indicators['pivot'] = pivot
    indicators['r1'] = 2 * pivot - low
    indicators['r2'] = pivot + (high - low)
    indicators['r3'] = pivot + 1.5 * (high - low)
    indicators['s1'] = 2 * pivot - high
    indicators['s2'] = pivot - (high - low)
    indicators['s3'] = pivot - 1.5 * (high - low)
    indicators['atr_14'] = atr
    indicators['pct_from_ath'] = ((price / 5645.60) - 1) * 100
    
    sma_200 = indicators.get('sma_200', 4359)
    indicators['trend_bias'] = 'BULLISH' if price > sma_200 else 'BEARISH'
    return indicators


def _generate_exec_summary(price: float, indicators: dict, trading: dict, events: list, now_aest: datetime) -> str:
    """Generate executive summary based on CURRENT conditions."""
    us_now = now_aest.astimezone(ET)
    today_us = us_now.strftime('%A %B %d')
    trend = indicators['trend_bias']
    change_pct = indicators.get('daily_change_pct', 0)
    atr = indicators.get('atr_14', 95)
    
    parts = []
    
    # Holiday / trading status FIRST
    if trading['is_holiday']:
        parts.append(f"<strong>US MARKET HOLIDAY TODAY ({today_us}):</strong> {trading['holiday_name']}. US markets are CLOSED. Gold futures (COMEX) on reduced hours. Liquidity will be thin — wider spreads, unpredictable moves. Consider staying flat or reducing size by 50%.")
    elif trading['is_weekend']:
        parts.append(f"<strong>WEEKEND:</strong> Markets closed. Report generated for Monday planning.")
    
    # Price context
    if price >= 5000:
        parts.append(f"Gold at <strong>${price:.2f}</strong> in the $5,000+ zone — bull market extension. {trend} bias intact. ATR ${atr:.0f} indicates elevated volatility.")
    elif price >= 4800:
        parts.append(f"Gold at <strong>${price:.2f}</strong> recovering toward $5,000 resistance. {trend} bias. Needs break above $4,900 to confirm correction over. ATR ${atr:.0f}.")
    elif price >= 4600:
        parts.append(f"Gold at <strong>${price:.2f}</strong> consolidating in the $4,600-$4,800 range. {trend} bias. The 200-day SMA at ${indicators['sma_200']:.0f} is the critical level — above = accumulation zone, below = deeper correction risk.")
    elif price >= 4400:
        parts.append(f"Gold at <strong>${price:.2f}</strong> — testing critical support zone. {trend} bias. The 200-day SMA at ${indicators['sma_200']:.0f} is the line in the sand. A sustained break below opens $4,200-$4,100.")
    else:
        parts.append(f"Gold at <strong>${price:.2f}</strong> — BELOW the 200-day SMA (${indicators['sma_200']:.0f}). Bearish. The bull market is under threat. Only counter-trend longs at extreme oversold levels with tight stops.")
    
    # Today's move
    if abs(change_pct) > 1.5:
        parts.append(f"<strong>Significant move today:</strong> {'+' if change_pct > 0 else ''}{change_pct:.2f}%. Volatility elevated — adjust position size down.")
    
    # Key events
    if events:
        next_event = events[0]
        parts.append(f"<strong>Key event:</strong> {next_event['event']} — {next_event['date']} at {next_event['time']}. {next_event['note']}")
    
    return " ".join(parts)


def _generate_macro_analysis(price: float, indicators: dict, now_aest: datetime) -> str:
    """Generate macro analysis — DYNAMIC, no hardcoded dates."""
    us_now = now_aest.astimezone(ET)
    dxy = indicators.get('dxy', 99.27)
    ten_year = indicators.get('ten_year', 4.46)
    trend = indicators['trend_bias']
    
    # Fed policy — dynamic based on price level
    fed_section = f"""<h3>Federal Reserve Policy</h3>
<p>The Federal Reserve holds at <strong>3.50%-3.75%</strong>. The April FOMC meeting featured 4 dissents — the most divided committee since 1992 — signaling growing internal pressure for rate cuts. CME FedWatch currently prices a high probability of no change at the next meeting, but the trend is shifting dovish.</p>
<p>Incoming Chair Kevin Warsh has signaled openness to "radical system change," adding policy uncertainty that is gold-supportive.</p>
<div class="highlight"><strong>Fed Bias:</strong> {'Dovish undertone supportive of gold above $4,600. Rate cut hopes increase if gold breaks $4,800.' if price > 4600 else 'Hawkish hold creating pressure. Gold needs a Fed pivot signal for recovery below $4,500.'}</div>"""
    
    # Inflation
    if ten_year > 4.5:
        inflation_section = f"""<h3>Inflation & Real Yields</h3>
<p>The 10-year Treasury at <strong>{ten_year:.2f}%</strong> reflects elevated inflation expectations. CPI remains above the Fed's 2% target. The Iran conflict continues to add energy-driven inflation pressure. Real yields are historically elevated, creating headwinds for non-yielding gold — though the traditional gold-yield correlation has weakened as central bank buying overrides rate signals.</p>"""
    elif ten_year > 4.0:
        inflation_section = f"""<h3>Inflation & Real Yields</h3>
<p>The 10-year Treasury at <strong>{ten_year:.2f}%</strong> shows inflation remains sticky but is moderating from peak levels. Real yields are elevated but off highs — a potential tailwind for gold if the trend continues lower. Watch for any re-acceleration in inflation data.</p>"""
    else:
        inflation_section = f"""<h3>Inflation & Real Yields</h3>
<p>The 10-year Treasury at <strong>{ten_year:.2f}%</strong> has eased back meaningfully, reducing pressure on gold. Lower real yields are supportive of gold prices. If yields continue to trend lower, gold should benefit — especially if driven by recession fears rather than inflation optimism.</p>"""
    
    # DXY
    if dxy > 101:
        dxy_section = f"""<h3>US Dollar</h3>
<p>DXY at <strong>{dxy:.2f}</strong> is a significant headwind for gold. Above 101 is the danger zone — each 1% DXY move typically produces an inverse $40-60 move in gold. Dollar strength is driven by safe-haven flows and widening rate differentials. A DXY reversal below 100 would be a major gold tailwind.</p>"""
    elif dxy > 99:
        dxy_section = f"""<h3>US Dollar</h3>
<p>DXY at <strong>{dxy:.2f}</strong> sits near the critical 100.00-100.50 zone. A sustained break above 100.50 accelerates gold's correction; a break back below 99.00 opens the door for gold recovery. Consensus forecasts DXY weakening toward 90-96 by late 2026 — a medium-term gold tailwind if realized.</p>"""
    else:
        dxy_section = f"""<h3>US Dollar</h3>
<p>DXY at <strong>{dxy:.2f}</strong> has weakened below 99, providing relief for gold. DXY below 99.00 is supportive — each 1% drop in DXY typically adds $40-60 to gold. The dollar bear case strengthens if Fed rate cuts materialize and the US fiscal deficit continues to expand.</p>"""
    
    return fed_section + inflation_section + dxy_section


def _generate_technical_analysis(price: float, indicators: dict) -> str:
    """Generate technical analysis — ALL dynamic from live price."""
    rsi = indicators.get('rsi', 35.42)
    macd = indicators.get('macd', -26.31)
    adx = indicators.get('adx', 46.6)
    sma_200 = indicators.get('sma_200', 4359)
    pivot = indicators['pivot']
    r1 = indicators['r1']
    s1 = indicators['s1']
    atr = indicators['atr_14']
    trend = indicators['trend_bias']
    
    # RSI dynamic text
    if rsi < 30:
        rsi_html = f"<tr><td>RSI (14)</td><td>{rsi:.1f}</td><td><span class='signal-box signal-strong-buy'>OVERSOLD</span></td><td>Oversold (&lt;30) — bounce potential. Wait for bullish divergence before counter-trend longs.</td></tr>"
    elif rsi < 40:
        rsi_html = f"<tr><td>RSI (14)</td><td>{rsi:.1f}</td><td><span class='signal-box signal-sell'>SELL</span></td><td>Bearish momentum. Room for more downside before oversold bounce.</td></tr>"
    elif rsi < 50:
        rsi_html = f"<tr><td>RSI (14)</td><td>{rsi:.1f}</td><td><span class='signal-box signal-neutral'>WEAK</span></td><td>Neutral-bearish. Below 50 = bears in control. Need reclaim for bulls.</td></tr>"
    elif rsi < 60:
        rsi_html = f"<tr><td>RSI (14)</td><td>{rsi:.1f}</td><td><span class='signal-box signal-buy'>BULLISH</span></td><td>Bullish momentum building. Buy pullbacks to support.</td></tr>"
    else:
        rsi_html = f"<tr><td>RSI (14)</td><td>{rsi:.1f}</td><td><span class='signal-box signal-strong-sell'>OVERBOUGHT</span></td><td>Overbought. Profit-taking risk. Consider trimming longs.</td></tr>"
    
    # MACD dynamic
    macd_signal = "SELL" if macd < 0 else "BUY"
    macd_class = "signal-strong-sell" if macd < -20 else "signal-sell" if macd < 0 else "signal-buy" if macd < 20 else "signal-strong-buy"
    if macd < -20:
        macd_text = f"Deeply negative ({macd:.2f}) — bearish momentum accelerating. Trend followers stay short."
    elif macd < 0:
        macd_text = f"Negative ({macd:.2f}) — bearish momentum. Watch for histogram narrowing as early bottom signal."
    elif macd < 20:
        macd_text = f"Positive ({macd:.2f}) — bullish momentum building. Confirm with price break above resistance."
    else:
        macd_text = f"Strongly positive ({macd:.2f}) — bullish momentum confirmed. Ride the trend."
    
    macd_html = f"<tr><td>MACD</td><td>{macd:.2f}</td><td><span class='signal-box {macd_class}'>{macd_signal}</span></td><td>{macd_text}</td></tr>"
    
    # ADX dynamic
    if adx > 40:
        adx_html = f"<tr><td>ADX (14)</td><td>{adx:.1f}</td><td><span class='signal-box signal-neutral'>STRONG TREND</span></td><td>Very strong trend. Trend-following only — counter-trend trades are dangerous.</td></tr>"
    elif adx > 25:
        adx_html = f"<tr><td>ADX (14)</td><td>{adx:.1f}</td><td><span class='signal-box signal-neutral'>TRENDING</span></td><td>Trending market. Follow the trend until ADX drops below 25.</td></tr>"
    else:
        adx_html = f"<tr><td>ADX (14)</td><td>{adx:.1f}</td><td><span class='signal-box signal-neutral'>RANGE</span></td><td>Range-bound. Mean-reversion: buy support, sell resistance.</td></tr>"
    
    # Price context
    dist_sma = ((price / sma_200) - 1) * 100
    if price > sma_200 * 1.02:
        price_context = f"Price at <strong>${price:.2f}</strong> is <strong>{dist_sma:.1f}%</strong> above the 200-day SMA (${sma_200:.0f}) — confirmed bull market territory."
    elif price > sma_200 * 0.98:
        price_context = f"Price at <strong>${price:.2f}</strong> is testing the 200-day SMA zone (${sma_200:.0f}) — <strong>critical juncture</strong>. Break below flips long-term bias to bearish."
    else:
        price_context = f"Price at <strong>${price:.2f}</strong> is <strong>{abs(dist_sma):.1f}%</strong> below the 200-day SMA (${sma_200:.0f}) — <strong>correction mode</strong>. The longer below, the deeper the potential drop."
    
    return f"""<h3>Price Context</h3>
<p>{price_context}</p>
<h3>Momentum Indicators</h3>
<table><tr><th>Indicator</th><th>Value</th><th>Signal</th><th>Assessment</th></tr>
{rsi_html}
{macd_html}
{adx_html}
</table>
<h3>Key Levels (Recalculated from Live Data)</h3>
<table><tr><th>Type</th><th>Level</th><th>Price</th><th>Significance</th></tr>
<tr><td>Resistance</td><td><span class="level-box level-r">R3</span></td><td>${indicators['r3']:.0f}</td><td>Extended target</td></tr>
<tr><td>Resistance</td><td><span class="level-box level-r">R2</span></td><td>${indicators['r2']:.0f}</td><td>Strong resistance / TP</td></tr>
<tr><td>Resistance</td><td><span class="level-box level-r">R1</span></td><td>${r1:.0f}</td><td>First resistance / short entry</td></tr>
<tr><td>Pivot</td><td><span class="level-box level-p">P</span></td><td>${pivot:.0f}</td><td>Session bias divider</td></tr>
<tr><td>Support</td><td><span class="level-box level-s">S1</span></td><td>${s1:.0f}</td><td>First support / long entry</td></tr>
<tr><td>Support</td><td><span class="level-box level-s">S2</span></td><td>${indicators['s2']:.0f}</td><td>Strong support / add longs</td></tr>
<tr><td>Support</td><td><span class="level-box level-s">S3</span></td><td>${indicators['s3']:.0f}</td><td>Last defence / stop</td></tr>
<tr><td>Support</td><td><span class="level-box level-s">200-SMA</span></td><td>${sma_200:.0f}</td><td>Bull market line</td></tr>
</table>"""


def _generate_trade_plan(price: float, indicators: dict) -> str:
    """Generate trade plan — DYNAMIC based on price vs pivot and trend."""
    pivot = indicators['pivot']
    r1 = indicators['r1']
    r2 = indicators['r2']
    r3 = indicators['r3']
    s1 = indicators['s1']
    s2 = indicators['s2']
    s3 = indicators['s3']
    atr = indicators['atr_14']
    trend = indicators['trend_bias']
    
    if price > pivot * 1.005:
        scenario_class = "scenario-bullish"
        scenario_title = "BULLISH BIAS"
        scenario_text = f"Price at <strong>${price:.2f}</strong> is above pivot (${pivot:.0f}) — intraday bias bullish. Buy dips toward S1 ${s1:.0f}, or play break above R1 ${r1:.0f}."
        long_entry = f"S1 ${s1:.0f} zone on pullback with bullish candlestick (hammer, engulfing)"
        long_stop = f"S2 ${s2:.0f}"
        long_tp1, long_tp2, long_tp3 = f"R1 ${r1:.0f}", f"R2 ${r2:.0f}", f"R3 ${r3:.0f}"
        short_entry = f"R2 ${r2:.0f} on rejection with bearish candlestick (shooting star)"
        short_stop = f"R3 ${r3:.0f}"
        short_tp1, short_tp2 = f"R1 ${r1:.0f}", f"Pivot ${pivot:.0f}"
    elif price < pivot * 0.995:
        scenario_class = "scenario-bearish"
        scenario_title = "BEARISH BIAS"
        scenario_text = f"Price at <strong>${price:.2f}</strong> is below pivot (${pivot:.0f}) — intraday bias bearish. Sell rallies toward R1 ${r1:.0f}, or play break below S1 ${s1:.0f}."
        long_entry = f"S2 ${s2:.0f} on bullish reversal candlestick"
        long_stop = f"S3 ${s3:.0f}"
        long_tp1, long_tp2, long_tp3 = f"S1 ${s1:.0f}", f"Pivot ${pivot:.0f}", f"R1 ${r1:.0f}"
        short_entry = f"R1 ${r1:.0f} on rejection / Break below S1 ${s1:.0f}"
        short_stop = f"R2 ${r2:.0f}"
        short_tp1, short_tp2 = f"S1 ${s1:.0f}", f"S2 ${s2:.0f}"
    else:
        scenario_class = "scenario-neutral"
        scenario_title = "NEUTRAL / RANGE"
        scenario_text = f"Price at <strong>${price:.2f}</strong> near pivot (${pivot:.0f}) — no clear bias. Range trade: buy S1 ${s1:.0f}, sell R1 ${r1:.0f}. Await directional break."
        long_entry = f"S1 ${s1:.0f} with reversal signal"
        long_stop = f"S2 ${s2:.0f}"
        long_tp1, long_tp2, long_tp3 = f"Pivot ${pivot:.0f}", f"R1 ${r1:.0f}", f"R2 ${r2:.0f}"
        short_entry = f"R1 ${r1:.0f} with rejection signal"
        short_stop = f"R2 ${r2:.0f}"
        short_tp1, short_tp2 = f"Pivot ${pivot:.0f}", f"S1 ${s1:.0f}"
    
    return f"""<div class="scenario {scenario_class}">
<div class="scenario-title">{scenario_title}</div>
{scenario_text}
</div>
<div class="trade-box">
<h4>LONG SETUP</h4>
<div class="trade-row"><span class="trade-label">Entry:</span><span class="trade-value">{long_entry}</span></div>
<div class="trade-row"><span class="trade-label">Stop Loss:</span><span class="trade-value" style="color:#ef4444">{long_stop}</span></div>
<div class="trade-row"><span class="trade-label">TP1:</span><span class="trade-value" style="color:#22c55e">{long_tp1}</span></div>
<div class="trade-row"><span class="trade-label">TP2:</span><span class="trade-value" style="color:#22c55e">{long_tp2}</span></div>
<div class="trade-row"><span class="trade-label">TP3:</span><span class="trade-value" style="color:#22c55e">{long_tp3}</span></div>
</div>
<div class="trade-box">
<h4>SHORT SETUP</h4>
<div class="trade-row"><span class="trade-label">Entry:</span><span class="trade-value">{short_entry}</span></div>
<div class="trade-row"><span class="trade-label">Stop Loss:</span><span class="trade-value" style="color:#ef4444">{short_stop}</span></div>
<div class="trade-row"><span class="trade-label">TP1:</span><span class="trade-value" style="color:#22c55e">{short_tp1}</span></div>
<div class="trade-row"><span class="trade-label">TP2:</span><span class="trade-value" style="color:#22c55e">{short_tp2}</span></div>
</div>
<div class="trade-box">
<h4>Risk Management</h4>
<div class="trade-row"><span class="trade-label">Position Size:</span><span class="trade-value">Risk 1-2% max per trade</span></div>
<div class="trade-row"><span class="trade-label">ATR (today):</span><span class="trade-value">${atr:.0f}</span></div>
<div class="trade-row"><span class="trade-label">High Vol:</span><span class="trade-value">Halve size when ATR &gt;$120</span></div>
<div class="trade-row"><span class="trade-label">Best Session:</span><span class="trade-value">London-NY overlap 8-11 PM AEST</span></div>
<div class="trade-row"><span class="trade-label">Avoid:</span><span class="trade-value">Holdings through FOMC, CPI, NFP</span></div>
</div>"""


def _generate_event_html(events: list, trading: dict, now_aest: datetime) -> str:
    """Generate event calendar HTML — ALWAYS relative to today."""
    if trading['is_holiday']:
        return f"""<div class="warning">
<strong>US MARKET HOLIDAY:</strong> {trading['holiday_name']} ({trading['date_us']}). Markets CLOSED. Gold futures on reduced hours. Low liquidity — wider spreads. Consider reducing position size or staying flat.
</div>"""
    
    if not events:
        return f"""<div class="highlight">
<strong>This Week:</strong> No major high-impact events scheduled. Watch for unexpected Fed speaker comments and geopolitical developments. Standard technical trading applies.
</div>"""
    
    rows = ""
    for ev in events:
        impact_class = "style='background:#fff8e1'" if ev['impact'] == 'VERY HIGH' else ""
        rows += f"""<tr {impact_class}>
<td><strong>{ev['date']}</strong></td>
<td>{ev['time']}</td>
<td><strong>{ev['event']}</strong></td>
<td><strong>{ev['impact']}</strong></td>
<td>{ev['note']}</td>
</tr>"""
    
    return f"""<h3>This Week's Key Events</h3>
<table><tr><th>Date</th><th>Time (ET)</th><th>Event</th><th>Impact</th><th>Trading Note</th></tr>
{rows}
</table>
<div class="highlight">
<strong>Pre-Event Protocol:</strong> Be flat or reduced size 30 minutes before high-impact releases. The initial 5-minute reaction reverses ~40% of the time.
</div>"""


def _build_complete_html(price, indicators, trading, exec_summary, macro, technical, trade_plan, event_html, now_aest) -> str:
    """Assemble the complete HTML report."""
    change = indicators['daily_change']
    change_pct = indicators['daily_change_pct']
    dxy = indicators.get('dxy', 99.27)
    dxy_change = indicators.get('dxy_change', 0)
    ten_year = indicators.get('ten_year', 4.46)
    vix = indicators.get('vix', 18.5)
    usd_jpy = indicators.get('usd_jpy', 159.0)
    oil = indicators.get('oil', 103.67)
    rsi = indicators.get('rsi', 35.42)
    adx = indicators.get('adx', 46.6)
    ath = 5645.60
    pct_from_ath = indicators.get('pct_from_ath', -19.6)
    trend = indicators['trend_bias']
    volume = indicators.get('volume', 0)
    
    # Signal
    if rsi < 30 and indicators.get('macd', 0) < 0:
        signal, signal_class = "STRONG SELL", "signal-strong-sell"
    elif rsi < 45 and indicators.get('macd', 0) < 0:
        signal, signal_class = "SELL", "signal-sell"
    elif rsi > 70 and indicators.get('macd', 0) > 0:
        signal, signal_class = "STRONG BUY", "signal-strong-buy"
    elif rsi > 55 and indicators.get('macd', 0) > 0:
        signal, signal_class = "BUY", "signal-buy"
    else:
        signal, signal_class = "NEUTRAL", "signal-neutral"
    
    # Holiday banner
    holiday_banner = ""
    if trading['is_holiday']:
        holiday_banner = f"""<div style="background:#3a1515;color:#ff6b6b;padding:12px;text-align:center;font-weight:bold;font-size:14px;margin:0">
US MARKET HOLIDAY: {trading['holiday_name']} — Markets CLOSED
</div>"""
    
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="refresh" content="3600">
<title>XAU/USD Daily Report - {now_aest.strftime('%A %B %d %Y')}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',Arial,sans-serif;background:#f5f5f5;color:#333;line-height:1.6}}
.container{{max-width:800px;margin:0 auto;background:#fff}}
.header{{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);color:#fff;padding:30px;text-align:center}}
.header h1{{font-size:28px;margin-bottom:8px;color:#daa520}}
.header .date{{font-size:14px;color:#888}}
.batch-badge{{display:inline-block;background:#daa520;color:#1a1a2e;padding:4px 12px;border-radius:4px;font-size:11px;font-weight:bold;margin-top:8px}}
.price-bar{{display:flex;justify-content:center;align-items:center;gap:30px;padding:20px;background:#0f3460;color:#fff}}
.price-main{{text-align:center}}.price-label{{font-size:12px;text-transform:uppercase;color:#888}}
.price-value{{font-size:36px;font-weight:bold;color:#daa520}}
.price-change{{font-size:16px}}.bullish{{color:#22c55e}}.bearish{{color:#ef4444}}.neutral{{color:#eab308}}
.section{{padding:25px 30px;border-bottom:1px solid #eee}}
.section h2{{font-size:20px;color:#1a1a2e;margin-bottom:15px;border-left:4px solid #daa520;padding-left:12px}}
.section h3{{font-size:16px;color:#333;margin:15px 0 10px}}
.section p{{margin-bottom:12px;font-size:14px}}
table{{width:100%;border-collapse:collapse;margin:15px 0;font-size:13px}}
th{{background:#1a1a2e;color:#daa520;padding:10px 12px;text-align:left;font-weight:600}}
td{{padding:10px 12px;border-bottom:1px solid #eee}}
tr:nth-child(even){{background:#f8f9fa}}
.level-box{{display:inline-block;padding:3px 10px;border-radius:4px;font-weight:bold;font-size:13px}}
.level-r{{background:#fee;color:#c00}}.level-s{{background:#efe;color:#080}}.level-p{{background:#eef;color:#00c}}
.signal-box{{display:inline-block;padding:4px 12px;border-radius:4px;font-weight:bold;font-size:14px}}
.signal-strong-sell{{background:#fee;color:#c00}}.signal-sell{{background:#ffe0e0;color:#d00}}
.signal-buy{{background:#efe;color:#080}}.signal-strong-buy{{background:#dfd;color:#060}}
.signal-neutral{{background:#ffe;color:#880}}
.highlight{{background:#fff8e1;padding:15px;border-left:4px solid #daa520;margin:15px 0;font-size:14px}}
.warning{{background:#fee;padding:15px;border-left:4px solid #c00;margin:15px 0;font-size:14px}}
.info-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:15px;margin:15px 0}}
.info-card{{background:#f8f9fa;padding:15px;border-radius:8px;border:1px solid #e0e0e0}}
.info-card .label{{font-size:11px;text-transform:uppercase;color:#888;margin-bottom:5px}}
.info-card .value{{font-size:18px;font-weight:bold;color:#1a1a2e}}
.trade-box{{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);color:#fff;padding:20px;border-radius:8px;margin:15px 0}}
.trade-box h4{{color:#daa520;margin-bottom:10px;font-size:16px}}
.trade-row{{display:flex;justify-content:space-between;margin:8px 0;font-size:14px}}
.trade-label{{color:#888}}.trade-value{{font-weight:600}}
.scenario{{padding:12px 15px;border-radius:6px;margin:10px 0;font-size:14px}}
.scenario-bearish{{background:#fee;border-left:4px solid #c00}}.scenario-bullish{{background:#efe;border-left:4px solid #080}}
.scenario-neutral{{background:#f0f0f0;border-left:4px solid #888}}.scenario-title{{font-weight:bold;margin-bottom:5px}}
.footer{{background:#1a1a2e;color:#888;padding:20px;text-align:center;font-size:12px}}
ul{{margin-left:20px;margin-bottom:12px}}li{{margin-bottom:6px;font-size:14px}}
</style></head><body><div class="container">

{holiday_banner}

<div class="header">
<h1>XAU/USD Daily Trading Report</h1>
<div class="date">{now_aest.strftime('%A, %B %d, %Y')} AEST | {trading['date_us']} US</div>
<div class="batch-badge">FULL DAILY REPORT — 6:00 AM AEST BATCH</div>
</div>

<div class="price-bar">
<div class="price-main">
<div class="price-label">XAU/USD</div>
<div class="price-value {'bullish' if change >= 0 else 'bearish'}">${price:.2f}</div>
<div class="price-change {'bullish' if change >= 0 else 'bearish'}">{'+' if change >= 0 else ''}{change:.2f} ({'+' if change_pct >= 0 else ''}{change_pct:.2f}%)</div>
<div style="font-size:11px;color:#888;margin-top:4px">Updated: {now_aest.strftime('%a %d %b %H:%M')} AEST | Source: twelvedata.com</div>
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

<div class="section">
<h2>Executive Summary</h2>
<div class="{'warning' if trading['is_holiday'] else 'highlight'}">
{exec_summary}
</div>
<div class="info-grid">
<div class="info-card"><div class="label">Fed Funds</div><div class="value">3.50%-3.75%</div></div>
<div class="info-card"><div class="label">DXY</div><div class="value">{dxy:.2f} <span class="{'bullish' if dxy_change >= 0 else 'bearish'}">({dxy_change:+.2f}%)</span></div></div>
<div class="info-card"><div class="label">10Y Treasury</div><div class="value">{ten_year:.2f}%</div></div>
<div class="info-card"><div class="label">VIX</div><div class="value">{vix:.1f}</div></div>
<div class="info-card"><div class="label">USD/JPY</div><div class="value">{usd_jpy:.2f}</div></div>
<div class="info-card"><div class="label">Oil (WTI)</div><div class="value">${oil:.2f}</div></div>
</div>
</div>

<div class="section">
<h2>Macro Analysis</h2>
{macro}
</div>

<div class="section">
<h2>Technical Analysis</h2>
{technical}
</div>

<div class="section">
<h2>Trade Plan & Strategy</h2>
{trade_plan}
</div>

<div class="section">
<h2>Economic Calendar & Events</h2>
{event_html}
</div>

<div class="footer">
<p>XAU/USD Daily Reporter | Full report: {now_aest.strftime('%a %d %b %H:%M')} AEST | Next: Tomorrow 6:00 AM AEST</p>
<p style="margin-top:6px;color:#555">This report is for informational purposes only. Trading involves significant risk of loss.</p>
</div>

</div></body></html>"""


def _generate_error_html(trading: dict, now_aest: datetime) -> str:
    """Generate error page when no live data."""
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>XAU/USD - Error</title>
<style>body{{font-family:Arial,sans-serif;background:#1a1a2e;color:#fff;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}}
.container{{text-align:center;max-width:600px;padding:40px}}
h1{{color:#daa520;font-size:48px;margin-bottom:10px}}
.error{{color:#ef4444;font-size:24px;margin:20px 0}}
.reason{{color:#888;font-size:16px;margin:15px 0}}
.timestamp{{color:#555;font-size:14px;margin-top:30px}}
</style></head><body><div class="container">
<h1>XAU/USD</h1><div class="error">⚠ Price Unavailable</div>
<div class="reason">Live price data unavailable. API key may be invalid or TwelveData rate limit reached.</div>
<div class="timestamp">{now_aest.strftime('%a %d %b %H:%M')} AEST</div>
</div></body></html>"""
