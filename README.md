# XAU/USD Daily Trading Report - Fully Automated

> **Your live dashboard is running at: https://r7w25pt4l54xw.kimi.page**
>
> Bookmark this link. It auto-refreshes every hour.

---

## What You Get Every Working Day (Mon-Fri) at 7:00 AM

1. **An email** with the full HTML report (if you add email credentials below)
2. **An updated web dashboard** at the link above (works immediately, no setup)
3. **Professional-grade analysis**: Macro, technical, sentiment, key levels, trade setups

---

## ZERO-SETUP Option: Web Dashboard Only

Just bookmark this link and check it every morning:

### 🔗 https://r7w25pt4l54xw.kimi.page

That's it. No accounts, no passwords, no configuration. It works right now.

**Limitation:** This hosted version updates when I regenerate it. For fully automated daily updates on YOUR schedule, see the self-hosted option below.

---

## Self-Hosted: Full Automation (Recommended)

Run this on your own computer or a $5/month VPS for fully automated daily reports.

### Quick Start (2 minutes)

```bash
# 1. Download and extract
cd ~/Desktop  # or wherever you want
# Extract the xauusd-reporter.zip file I provided

# 2. Install (one command)
./setup.sh

# 3. Start the daily scheduler
./run.sh schedule
```

That's it. It will now generate and update the report every weekday at 7:00 AM.

### To get EMAIL delivery too:

**Option A: SendGrid (Recommended - Simplest)**

1. Go to https://signup.sendgrid.com → Sign up free (30 seconds, no credit card)
2. Verify your email
3. Go to https://app.sendgrid.com/settings/api_keys → "Create API Key"
4. Copy the key (starts with `SG.xxxxx`)
5. Open `.env` file and paste:
   ```
   SENDGRID_API_KEY=SG.your-key-here
   ```
6. Restart: `./run.sh schedule`

**Option B: Gmail**
1. Go to https://myaccount.google.com/apppasswords
2. Generate an App Password
3. Open `.env` file and add:
   ```
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   ```

---

## Commands

| Command | What it does |
|---------|-------------|
| `./run.sh schedule` | Start daily auto-reports (Mon-Fri 7 AM) |
| `./run.sh now` | Generate and send report immediately |
| `./run.sh test` | Test email configuration |
| `./run.sh web` | Generate web report only (no email) |
| `./run.sh docker` | Run in Docker container |

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

## Technical Stack

- **Data:** Yahoo Finance (free, no API key needed)
- **Web:** Auto-generated HTML, deployed to cloud
- **Email:** SendGrid API (free tier: 100 emails/day)
- **Schedule:** APScheduler (cron, Mon-Fri only)
- **Language:** Python 3.11+

---

## Troubleshooting

**"Rate limited" errors?**
- Normal in shared environments. On your own machine it works fine.
- The app auto-retries 3 times with delays.

**Email not sending?**
- Check `./run.sh test` to verify config
- With SendGrid: verify the API key starts with `SG.`
- With Gmail: must use App Password, not regular password

**Want a different time?**
- Edit `.env` and change `REPORT_TIME=07:00` to your preferred time (24h format)

---

## Files Included

```
xauusd-reporter/
├── app/
│   ├── main.py              # Entry point (run/schedule/test/web)
│   ├── data_fetcher.py      # Live market data (yfinance)
│   ├── report_generator.py  # HTML email report
│   ├── email_sender.py      # Gmail SMTP sender
│   ├── sendgrid_sender.py   # SendGrid API sender (recommended)
│   └── scheduler.py         # Daily job scheduler
├── config/settings.py       # Configuration
├── web/index.html           # Live dashboard
├── background_runner.py     # Background process runner
├── setup.sh                 # One-command setup
├── run.sh                   # One-command runner
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker container
├── docker-compose.yml       # Docker deployment
└── .env                     # Your config (created by setup.sh)
```

---

## Disclaimer

This report is for **informational purposes only** and does not constitute investment advice. Trading involves significant risk of loss. Past performance is not indicative of future results. Always conduct your own analysis before making trading decisions.

---

Built for Gorjan Ivanovski.
