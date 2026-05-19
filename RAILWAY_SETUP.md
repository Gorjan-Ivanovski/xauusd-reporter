# Deploy XAU/USD Reporter to Railway

## Step 1: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub (free tier included)

## Step 2: Create New Project
1. Click "New Project" 
2. Choose "Deploy from GitHub repo"
3. If repo not linked: Click "Configure GitHub App" and give Railway access

## Step 3: Upload Code to GitHub
```bash
# Option A: Create new repo and push
git init
git add .
git commit -m "Initial XAU/USD reporter"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/xauusd-reporter.git
git push -u origin main

# Option B: Upload via Railway CLI
# Install Railway CLI: npm i -g @railway/cli
# railway login
# railway init
```

## Step 4: Deploy
1. In Railway, select your repo
2. Railway auto-detects the Dockerfile
3. Click "Deploy" — it builds and deploys automatically

## Step 5: Set Environment Variables
In Railway dashboard → Variables tab, add:

| Variable | Value | Description |
|----------|-------|-------------|
| `GOLDAPI_KEY` | `goldapi-9d90dfd0fb5478f8719751976d3d84a6-io` | Gold API key (already set) |
| `SENDGRID_API_KEY` | *(your key)* | For email delivery (optional) |
| `RECIPIENT_EMAIL` | `Gorjan.ivanovski@gmail.com` | Email recipient |
| `PORT` | `8080` | Server port (auto-set by Railway) |

## Step 6: Get Your URL
Railway gives you a free domain like:
`https://xauusd-reporter.up.railway.app`

This URL works 24/7 with live prices updating every 5 minutes during market hours.

## Features on Railway

| Feature | Status |
|---------|--------|
| Live price updates | ✅ Every 5 min during market hours |
| Web dashboard | ✅ Served directly from container |
| API endpoint | ✅ `/api/price` returns JSON |
| Auto-restart | ✅ Always-on |
| Free tier | ✅ $5/month credit covers this |
| Email reports | ✅ Add SendGrid API key |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `/` | Main dashboard (HTML) |
| `/api/price` | Current price JSON |
| `/api/status` | Health check |
| `/trigger-update` | Force refresh |

## Free Tier Limits
- 500 hours/month runtime (enough for 24/7)
- $5 credit covers small projects
- Add credit card for unlimited
