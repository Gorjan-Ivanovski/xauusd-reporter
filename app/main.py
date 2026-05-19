"""Main entry point for XAU/USD Daily Reporter."""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from loguru import logger

from app.data_fetcher import MarketDataFetcher
from app.report_generator import ReportGenerator

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>"
)
log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'reporter.log')
logger.add(log_file, rotation="1 day", retention="7 days", level="DEBUG")


def _get_sender():
    """Get the best available email sender (SendGrid > SMTP)."""
    # Try SendGrid first
    from app.sendgrid_sender import SendGridSender
    sg = SendGridSender()
    if sg.api_key:
        logger.info("Using SendGrid for email delivery")
        return sg

    # Fall back to SMTP
    from app.email_sender import EmailSender
    smtp = EmailSender()
    if smtp.user and smtp.password:
        logger.info("Using SMTP for email delivery")
        return smtp

    return None


def generate_and_send_report():
    """Generate and send the daily XAU/USD report."""
    logger.info("=" * 60)
    logger.info("Starting XAU/USD Daily Report Generation")
    logger.info("=" * 60)

    try:
        # Step 1: Fetch market data
        logger.info("Step 1/4: Fetching market data...")
        fetcher = MarketDataFetcher()
        data, indicators = fetcher.fetch_all()

        if not indicators:
            logger.error("Failed to fetch market data. Aborting.")
            return False

        # Step 2: Generate report
        logger.info("Step 2/4: Generating report...")
        generator = ReportGenerator()
        html_report = generator.generate(indicators, data)
        text_report = generator.generate_text_version(indicators)

        # Save report to web directory for dashboard access
        _save_web_report(html_report)

        # Step 3: Send email
        logger.info("Step 3/4: Sending email...")
        sender = _get_sender()

        if sender is None:
            logger.warning("No email sender configured. Report saved to web/ directory only.")
            logger.warning("To enable email, configure SendGrid (recommended) or SMTP in .env")
            # Still return True since we saved the web report
            return True

        date_str = datetime.now().strftime('%B %d, %Y')
        success = sender.send_report(html_report, text_report, date_str)

        if success:
            logger.info("Step 4/4: Report delivered successfully!")
        else:
            logger.error("Step 4/4: Failed to deliver report via email (saved to web/)")

        logger.info("=" * 60)
        return success

    except Exception as e:
        logger.exception(f"Error in report generation: {e}")
        return False


def _save_web_report(html_content: str):
    """Save report to web directory for dashboard viewing."""
    web_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'web')
    os.makedirs(web_dir, exist_ok=True)

    # Save as index.html (latest report)
    index_path = os.path.join(web_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Save with timestamp (archive)
    timestamp = datetime.now().strftime('%Y%m%d')
    archive_path = os.path.join(web_dir, f'report_{timestamp}.html')
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    logger.info(f"Report saved to {index_path}")
    return index_path


def generate_web_only():
    """Generate report for web dashboard only (no email)."""
    logger.info("Generating web report (no email)...")

    try:
        fetcher = MarketDataFetcher()
        data, indicators = fetcher.fetch_all()

        generator = ReportGenerator()

        # Use default indicators if fetch fails
        if not indicators:
            logger.warning("Using default research-based indicators")
            indicators = {
                'current_price': 4540.00, 'daily_change': -32.50,
                'daily_change_pct': -0.71, 'ath': 5645.60, 'pct_from_ath': -19.6,
                'rsi': 35.42, 'adx': 46.6, 'macd': -26.31, 'dxy': 99.27,
                'dxy_change': 0.15, 'ten_year': 4.46, 'vix': 18.5,
                'usd_jpy': 159.0, 'oil': 103.67, 'r1': 4633, 'r2': 4725,
                'r3': 4785, 'pivot': 4557, 's1': 4480, 's2': 4420,
                's3': 4328, 'sma_200': 4359, 'atr_14': 95,
            }

        html_report = generator.generate(indicators, data)
        path = _save_web_report(html_report)
        logger.info(f"Web report saved: {path}")
        return path

    except Exception as e:
        logger.exception(f"Error generating web report: {e}")
        return None


def test_email():
    """Test email configuration."""
    # Try SendGrid first
    from app.sendgrid_sender import SendGridSender
    sg = SendGridSender()
    if sg.api_key and sg.verify_key():
        print("\nSendGrid configuration verified!")
        print(f"Recipients: {sg.recipients}")
        return True

    # Try SMTP
    from app.email_sender import EmailSender
    smtp = EmailSender()
    if smtp.test_connection():
        print("\nSMTP configuration verified!")
        print(f"Recipients: {smtp.recipients}")
        return True

    print("\nNo email sender configured.")
    print("Options:")
    print("  1. SendGrid (recommended): Set SENDGRID_API_KEY in .env")
    print("     Sign up free: https://signup.sendgrid.com")
    print("  2. Gmail SMTP: Set SMTP_USER and SMTP_PASSWORD in .env")
    return False


def run_now():
    """Run report generation immediately."""
    success = generate_and_send_report()
    sys.exit(0 if success else 1)


def schedule_daily():
    """Start daily scheduler."""
    from app.scheduler import ReportScheduler
    logger.info("Starting daily scheduler...")
    scheduler = ReportScheduler(generate_and_send_report)
    scheduler.start()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='XAU/USD Daily Reporter')
    parser.add_argument(
        'command',
        choices=['run', 'schedule', 'test', 'web'],
        help='Command: run=send now, schedule=daily at 7AM, test=test email, web=generate web only'
    )
    args = parser.parse_args()

    if args.command == 'test':
        test_email()
    elif args.command == 'run':
        run_now()
    elif args.command == 'schedule':
        schedule_daily()
    elif args.command == 'web':
        path = generate_web_only()
        if path:
            print(f"\nWeb report generated: {path}")
        else:
            sys.exit(1)


if __name__ == '__main__':
    main()
