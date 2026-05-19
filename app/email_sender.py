"""Email sender for XAU/USD daily report."""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from typing import List
from loguru import logger

from config.settings import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, RECIPIENT_EMAIL


class EmailSender:
    """Sends XAU/USD daily reports via SMTP."""

    def __init__(self):
        self.host = SMTP_HOST
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
        self.recipients = [e.strip() for e in RECIPIENT_EMAIL.split(',')]

    def send_report(self, html_content: str, text_content: str, date_str: str = None) -> bool:
        """Send the daily report email."""
        if not self.user or not self.password:
            logger.error("SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
            return False

        if date_str is None:
            date_str = datetime.now().strftime('%B %d, %Y')

        subject = f"XAU/USD Daily Report — {date_str}"

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = formataddr(('XAU/USD Reporter', self.user))
        msg['To'] = ', '.join(self.recipients)

        # Attach text and HTML versions
        part_text = MIMEText(text_content, 'plain', 'utf-8')
        part_html = MIMEText(html_content, 'html', 'utf-8')

        msg.attach(part_text)
        msg.attach(part_html)

        try:
            context = ssl.create_default_context()

            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls(context=context)
                server.login(self.user, self.password)
                server.sendmail(self.user, self.recipients, msg.as_string())

            logger.info(f"Report sent successfully to {', '.join(self.recipients)}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check your email and app password.")
            logger.error("For Gmail: Use an App Password from https://myaccount.google.com/apppasswords")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def test_connection(self) -> bool:
        """Test SMTP connection without sending."""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls(context=context)
                server.login(self.user, self.password)
                logger.info("SMTP connection test successful")
                return True
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False
