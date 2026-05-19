# XAU/USD Daily Trading Report - Fully Automated

**Live data from TwelveData | AEST timestamps | Updates every 5 minutes during market hours**

---

## Quick Start

### 1. Get a TwelveData API Key (free)
1. Go to https://twelvedata.com/pricing
2. Sign up for the **Free** plan (800 API calls/day)
3. Copy your API key from the dashboard

### 2. Deploy to Railway
1. Railway dashboard --> **New Project** --> **Deploy from GitHub repo**
2. Select `Gorjan-Ivanovski/xauusd-reporter`
3. Add environment variable:
   ```
   TWELVEDATA_API_KEY = your-key-here
   ```
4. Railway auto-builds from `Dockerfile` and deploys
5. Your URL will be: `https://xauusd-reporter.up.railway.app`

### 3. Bookmark Your Live Dashboard
The dashboard updates **once per hour** during market hours (8 AM - 6 PM AEST, Mon-Fri).

---

## What's in the Daily Report

1. **Executive Summary** - Bias, key levels, critical events at a glance
2. **Macro Analysis** - Fed policy, inflation (CPI/PCE), DXY, real yields
3. **Technical Analysis** - RSI, MACD, ADX, Bollinger, pivot points, MAs
4. **Key Levels** - Exact support/resistance with price targets
5. **Sentiment** - COT positioning, retail % long, ETF flows
6. **Geopolitical** - Active risks, economic calendar
7. **Trade Plan** - Entry, stop, target levels with risk/reward ratios
8. **Cross-Market Watch** - DXY, VIX, yields, oil correlations

---

## Data Source: TwelveData

- **Free tier:** 800 API calls/day (polling once per hour = ~84 calls/day)
- **Symbol:** XAU/USD
- **Latency:** Real-time
- **AEST timestamps:** All times shown in Australia/Sydney timezone

---

## Optional: Email Delivery

Add a SendGrid API key for email delivery:
1. https://signup.sendgrid.com --> sign up free
2. Create API key at https://app.sendgrid.com/settings/api_keys
3. Add to Railway environment variables:
   ```
   SENDGRID_API_KEY = SG.your-key-here
   RECIPIENT_EMAIL = Gorjan.ivanovski@gmail.com
   ```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TWELVEDATA_API_KEY` | Yes | Your TwelveData API key |
| `SENDGRID_API_KEY` | No | For email reports (optional) |
| `RECIPIENT_EMAIL` | No | Email recipient (optional) |
| `PORT` | Auto | Server port (Railway sets this) |

---

## Files

```
xauusd-reporter/
├── app/
│   ├── server.py              # Flask web server + background updater
│   ├── twelvedata_fetcher.py  # Live gold price from TwelveData
│   ├── report_generator.py    # HTML report builder (AEST timestamps)
│   ├── goldapi_fetcher.py     # GoldAPI (fallback, unused)
│   └── ...
├── Dockerfile                 # Railway auto-detects this
├── railway.toml               # Railway config
└── requirements.txt
```

---

## Disclaimer

This report is for **informational purposes only** and does not constitute investment advice. Trading involves significant risk of loss. Past performance is not indicative of future results.

---

Built for Gorjan Ivanovski.
