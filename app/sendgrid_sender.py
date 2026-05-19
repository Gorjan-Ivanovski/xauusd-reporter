"""SendGrid email sender for XAU/USD daily report."""
from datetime import datetime
from typing import List
from loguru import logger

from config.settings import RECIPIENT_EMAIL


class SendGridSender:
    """Sends XAU/USD daily reports via SendGrid API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or self._load_api_key()
        self.recipients = [e.strip() for e in RECIPIENT_EMAIL.split(',')]

    def _load_api_key(self) -> str:
        """Load API key from environment or file."""
        import os
        # Try environment variable
        key = os.getenv('SENDGRID_API_KEY', '')
        if key:
            return key
        # Try file
        key_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.sendgrid_key')
        if os.path.exists(key_file):
            with open(key_file, 'r') as f:
                return f.read().strip()
        return ''

    def send_report(self, html_content: str, text_content: str, date_str: str = None) -> bool:
        """Send the daily report email via SendGrid."""
        if not self.api_key:
            logger.error("SendGrid API key not configured.")
            logger.error("1. Sign up free at https://signup.sendgrid.com")
            logger.error("2. Create an API key at https://app.sendgrid.com/settings/api_keys")
            logger.error("3. Set SENDGRID_API_KEY in your .env file")
            return False

        if not self.api_key.startswith('SG.'):
            logger.error("Invalid SendGrid API key. Should start with 'SG.'")
            return False

        if date_str is None:
            date_str = datetime.now().strftime('%B %d, %Y')

        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Email, Content, MimeType, Personalization

            sg = SendGridAPIClient(self.api_key)

            # Build email
            mail = Mail(
                from_email=Email('noreply@xauusd-reporter.local', 'XAU/USD Reporter'),
                subject=f"XAU/USD Daily Report — {date_str}",
                html_content=html_content,
                plain_text_content=text_content,
            )

            # Add recipients
            for recipient in self.recipients:
                mail.add_to(Email(recipient))

            # Send
            response = sg.client.mail.send.post(request_body=mail.get())

            if response.status_code in (200, 201, 202):
                logger.info(f"Report sent successfully to {', '.join(self.recipients)} via SendGrid")
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code} — {response.body}")
                return False

        except ImportError:
            logger.error("sendgrid package not installed. Run: pip install sendgrid")
            return False
        except Exception as e:
            logger.error(f"Failed to send via SendGrid: {e}")
            return False

    def verify_key(self) -> bool:
        """Verify the API key works."""
        if not self.api_key:
            return False
        try:
            from sendgrid import SendGridAPIClient
            sg = SendGridAPIClient(self.api_key)
            # Try to get account info
            response = sg.client.user.profile.get()
            if response.status_code == 200:
                import json
                profile = json.loads(response.body)
                logger.info(f"SendGrid key verified: {profile.get('email', 'unknown')}")
                return True
            return False
        except Exception as e:
            logger.error(f"SendGrid key verification failed: {e}")
            return False
