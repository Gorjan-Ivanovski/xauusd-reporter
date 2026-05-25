"""US market holiday detection for trading schedule awareness."""
from datetime import datetime, timedelta
import pytz

AEST = pytz.timezone('Australia/Sydney')
ET = pytz.timezone('US/Eastern')


def get_us_holidays(year: int) -> dict:
    """Return US market holidays for a given year."""
    holidays = {}
    
    # New Year's Day
    ny = datetime(year, 1, 1)
    holidays[ny.strftime('%Y-%m-%d')] = "New Year's Day"
    if ny.weekday() == 6:  # Sunday
        holidays[(ny + timedelta(days=1)).strftime('%Y-%m-%d')] = "New Year's Day (Observed)"
    
    # Martin Luther King Jr. Day (3rd Monday in Jan)
    mlk = datetime(year, 1, 15)
    while mlk.weekday() != 0:
        mlk += timedelta(days=1)
    holidays[mlk.strftime('%Y-%m-%d')] = "Martin Luther King Jr. Day"
    
    # Presidents' Day (3rd Monday in Feb)
    pres = datetime(year, 2, 15)
    while pres.weekday() != 0:
        pres += timedelta(days=1)
    holidays[pres.strftime('%Y-%m-%d')] = "Presidents' Day"
    
    # Good Friday (calculated via Easter)
    good_friday = calculate_good_friday(year)
    if good_friday:
        holidays[good_friday.strftime('%Y-%m-%d')] = "Good Friday"
    
    # Memorial Day (last Monday in May)
    memorial = datetime(year, 5, 25)
    while memorial.weekday() != 0:
        memorial += timedelta(days=1)
    holidays[memorial.strftime('%Y-%m-%d')] = "Memorial Day"
    
    # Juneteenth (June 19, observed)
    june = datetime(year, 6, 19)
    holidays[june.strftime('%Y-%m-%d')] = "Juneteenth"
    if june.weekday() == 5:
        holidays[(june + timedelta(days=2)).strftime('%Y-%m-%d')] = "Juneteenth (Observed)"
    elif june.weekday() == 6:
        holidays[(june + timedelta(days=1)).strftime('%Y-%m-%d')] = "Juneteenth (Observed)"
    
    # Independence Day
    july4 = datetime(year, 7, 4)
    holidays[july4.strftime('%Y-%m-%d')] = "Independence Day"
    if july4.weekday() == 5:
        holidays[(july4 - timedelta(days=1)).strftime('%Y-%m-%d')] = "Independence Day (Observed)"
    elif july4.weekday() == 6:
        holidays[(july4 + timedelta(days=1)).strftime('%Y-%m-%d')] = "Independence Day (Observed)"
    
    # Labor Day (1st Monday in Sep)
    labor = datetime(year, 9, 1)
    while labor.weekday() != 0:
        labor += timedelta(days=1)
    holidays[labor.strftime('%Y-%m-%d')] = "Labor Day"
    
    # Thanksgiving (4th Thursday in Nov)
    thanksgiving = datetime(year, 11, 22)
    while thanksgiving.weekday() != 3:
        thanksgiving += timedelta(days=1)
    holidays[thanksgiving.strftime('%Y-%m-%d')] = "Thanksgiving"
    
    # Christmas
    xmas = datetime(year, 12, 25)
    holidays[xmas.strftime('%Y-%m-%d')] = "Christmas Day"
    if xmas.weekday() == 5:
        holidays[(xmas - timedelta(days=1)).strftime('%Y-%m-%d')] = "Christmas (Observed)"
    elif xmas.weekday() == 6:
        holidays[(xmas + timedelta(days=1)).strftime('%Y-%m-%d')] = "Christmas (Observed)"
    
    return holidays


def calculate_good_friday(year: int) -> datetime:
    """Calculate Good Friday date."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    easter = datetime(year, month, day)
    return easter - timedelta(days=2)


def is_us_market_holiday(date: datetime = None) -> tuple:
    """Check if given date (AEST) is a US market holiday.
    Returns (is_holiday, holiday_name)"""
    if date is None:
        date = datetime.now(AEST)
    
    # Convert to US date for holiday check
    us_date = date.astimezone(ET)
    date_str = us_date.strftime('%Y-%m-%d')
    
    holidays = get_us_holidays(us_date.year)
    
    if date_str in holidays:
        return True, holidays[date_str]
    
    return False, ""


def get_trading_status() -> dict:
    """Get full trading status for today."""
    now_aest = datetime.now(AEST)
    us_now = now_aest.astimezone(ET)
    
    is_holiday, holiday_name = is_us_market_holiday(now_aest)
    is_weekend = us_now.weekday() >= 5
    
    # Market hours in AEST
    # US pre-market: 11:00 PM - 1:30 AM AEST (next day)
    # US regular: 1:30 AM - 8:00 AM AEST
    # US after-hours: 8:00 AM - 9:55 AM AEST
    
    hour = now_aest.hour
    minute = now_aest.minute
    time_val = hour + minute / 60
    
    if is_holiday:
        market_status = "CLOSED"
        session = f"US Holiday: {holiday_name}"
        session_detail = f"Markets are closed today for {holiday_name}. No trading. Gold futures (COMEX) resume Tuesday 11:00 PM AEST."
    elif is_weekend:
        market_status = "CLOSED"
        session = "Weekend"
        next_open = now_aest + timedelta(days=(7 - now_aest.weekday()) % 7 or 7)
        session_detail = f"Markets closed for the weekend. Gold futures reopen Sunday 11:00 PM AEST."
    elif time_val < 1.5:
        market_status = "CLOSED"
        session = "US Overnight"
        session_detail = "US markets closed. Pre-market opens 11:00 PM AEST."
    elif time_val < 13.0:
        market_status = "OPEN"
        session = "US Regular Hours"
        session_detail = "NYSE/NASDAQ open. Gold futures active. Peak volatility during US session."
    elif time_val < 15.0:
        market_status = "OPEN"
        session = "US Pre-Market"
        session_detail = "US pre-market session. Lower liquidity, gap risk on earnings/news."
    else:
        market_status = "AFTER-HOURS"
        session = "US After-Hours"
        session_detail = "US after-hours. Thin liquidity. Wait for next session clarity."
    
    return {
        'is_holiday': is_holiday,
        'holiday_name': holiday_name,
        'is_weekend': is_weekend,
        'market_status': market_status,
        'session': session,
        'session_detail': session_detail,
        'date_aest': now_aest.strftime('%A, %B %d, %Y'),
        'date_us': us_now.strftime('%A, %B %d, %Y'),
    }


def get_this_week_events(now_aest: datetime) -> list:
    """Generate this week's key economic events relative to today."""
    events = []
    us_now = now_aest.astimezone(ET)
    
    # Always include the nearest FOMC meeting info
    # FOMC meetings are typically every 6 weeks
    # Next known meeting dates (approximate)
    fomc_dates_2026 = [
        datetime(2026, 1, 28), datetime(2026, 3, 18), datetime(2026, 5, 6),
        datetime(2026, 6, 17), datetime(2026, 7, 29), datetime(2026, 9, 16),
        datetime(2026, 10, 28), datetime(2026, 12, 16),
    ]
    
    next_fomc = None
    for fomc_date in fomc_dates_2026:
        if fomc_date.date() >= us_now.date():
            next_fomc = fomc_date
            break
    
    if next_fomc:
        days_until = (next_fomc.date() - us_now.date()).days
        if days_until == 0:
            events.append({
                'date': 'TODAY',
                'time': '2:00 PM ET',
                'event': 'FOMC Meeting Decision',
                'impact': 'VERY HIGH',
                'note': 'Rate decision today. Be flat by 1:30 PM ET. Expect $30-50 volatility.'
            })
        elif days_until <= 5:
            dow = next_fomc.strftime('%A')
            events.append({
                'date': f'{dow} ({days_until} days)',
                'time': '2:00 PM ET',
                'event': 'FOMC Meeting Decision',
                'impact': 'VERY HIGH',
                'note': f'Rate decision in {days_until} days. Reduce position size ahead of the meeting.'
            })
    
    # Monthly NFP (first Friday of each month)
    # Check if we're near month-end for NFP
    first_friday = datetime(us_now.year, us_now.month, 1)
    while first_friday.weekday() != 4:
        first_friday += timedelta(days=1)
    
    days_to_nfp = (first_friday.date() - us_now.date()).days
    if 0 <= days_to_nfp <= 7:
        events.append({
            'date': f'First Friday ({days_to_nfp} days)' if days_to_nfp > 0 else 'THIS FRIDAY',
            'time': '8:30 AM ET',
            'event': 'Non-Farm Payrolls (NFP)',
            'impact': 'VERY HIGH',
            'note': f'NFP in {days_to_nfp} days. >200K jobs = bearish gold (Fed hawkish). <150K = bullish.'
        })
    
    # CPI (monthly, typically mid-month)
    cpi_day = datetime(us_now.year, us_now.month, 13)
    while cpi_day.weekday() >= 5:
        cpi_day += timedelta(days=1)
    days_to_cpi = (cpi_day.date() - us_now.date()).days
    if 0 <= days_to_cpi <= 10:
        events.append({
            'date': f'{cpi_day.strftime("%A %d %b")} ({days_to_cpi} days)' if days_to_cpi > 0 else 'TODAY',
            'time': '8:30 AM ET',
            'event': 'CPI Inflation Report',
            'impact': 'VERY HIGH',
            'note': f'CPI in {days_to_cpi} days. Above 3.5% YoY = bearish gold. Below 3.0% = bullish.'
        })
    
    # PPI (day after CPI typically)
    ppi_day = cpi_day + timedelta(days=1)
    days_to_ppi = (ppi_day.date() - us_now.date()).days
    if 0 <= days_to_ppi <= 10:
        events.append({
            'date': f'{ppi_day.strftime("%A %d %b")} ({days_to_ppi} days)' if days_to_ppi > 0 else 'TODAY',
            'time': '8:30 AM ET',
            'event': 'PPI Producer Prices',
            'impact': 'HIGH',
            'note': f'PPI in {days_to_ppi} days. Second reading on inflation pipeline.'
        })
    
    # Retail Sales (mid-month)
    retail_day = datetime(us_now.year, us_now.month, 15)
    while retail_day.weekday() >= 5:
        retail_day += timedelta(days=1)
    days_to_retail = (retail_day.date() - us_now.date()).days
    if 0 <= days_to_retail <= 10:
        events.append({
            'date': f'{retail_day.strftime("%A %d %b")} ({days_to_retail} days)' if days_to_retail > 0 else 'TODAY',
            'time': '8:30 AM ET',
            'event': 'Retail Sales',
            'impact': 'HIGH',
            'note': f'Strong retail = hawkish Fed = bearish gold. Weak = dovish = bullish.'
        })
    
    return events
