#!/bin/bash
# XAU/USD Daily Reporter - Setup Script
# Run this script to set up and start the daily report service

set -e

echo "============================================"
echo "  XAU/USD Daily Reporter - Setup"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.11+ first.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Python version: $PYTHON_VERSION${NC}"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}=== Email Configuration ===${NC}"
    echo "This reporter sends daily XAU/USD reports via email."
    echo ""
    
    read -p "Enter your Gmail address (for sending): " SMTP_USER
    read -sp "Enter your Gmail App Password: " SMTP_PASSWORD
    echo ""
    read -p "Enter recipient email [Gorjan.ivanovski@gmail.com]: " RECIPIENT
    RECIPIENT=${RECIPIENT:-Gorjan.ivanovski@gmail.com}
    read -p "Enter report time [07:00]: " REPORT_TIME
    REPORT_TIME=${REPORT_TIME:-07:00}
    read -p "Enter timezone [Europe/Skopje]: " TIMEZONE
    TIMEZONE=${TIMEZONE:-Europe/Skopje}
    
    cat > .env << EOF
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=$SMTP_USER
SMTP_PASSWORD=$SMTP_PASSWORD
RECIPIENT_EMAIL=$RECIPIENT
REPORT_TIME=$REPORT_TIME
TIMEZONE=$TIMEZONE
EOF
    
    echo -e "${GREEN}Configuration saved to .env${NC}"
else
    echo -e "${GREEN}.env file already exists. Using existing configuration.${NC}"
fi

# Create logs directory
mkdir -p logs

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Available commands:"
echo "  ./run.sh test      - Test email configuration"
echo "  ./run.sh now       - Send report now (one-time)"
echo "  ./run.sh schedule  - Start daily scheduler (Mon-Fri at $REPORT_TIME)"
echo "  ./run.sh docker    - Run with Docker"
echo ""
