"""Scheduler for XAU/USD daily report."""
import pytz
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger

from config.settings import REPORT_TIME, TIMEZONE, WORKING_DAYS


class ReportScheduler:
    """Schedules the daily XAU/USD report generation and delivery."""

    def __init__(self, job_function):
        self.job_function = job_function
        self.scheduler = BlockingScheduler(timezone=pytz.timezone(TIMEZONE))

        # Parse report time
        try:
            hour, minute = map(int, REPORT_TIME.split(':'))
        except ValueError:
            hour, minute = 7, 0
            logger.warning(f"Invalid REPORT_TIME format: {REPORT_TIME}, defaulting to 07:00")

        self.hour = hour
        self.minute = minute

    def start(self):
        """Start the scheduler."""
        logger.info(f"Scheduling report for {self.hour:02d}:{self.minute:02d} "
                   f"{TIMEZONE} on weekdays (Mon-Fri)")

        # Add job: every working day at specified time
        self.scheduler.add_job(
            self.job_function,
            trigger=CronTrigger(
                hour=self.hour,
                minute=self.minute,
                day_of_week='mon-fri'  # Monday=0, Friday=4
            ),
            id='xauusd_daily_report',
            name='XAU/USD Daily Report',
            replace_existing=True,
            misfire_grace_time=3600  # 1 hour grace period
        )

        # Add a startup job for immediate testing
        # self.scheduler.add_job(self.job_function, 'date', run_date=datetime.now())

        logger.info("Scheduler started. Press Ctrl+C to exit.")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")
            self.scheduler.shutdown()

    def run_now(self):
        """Run the job immediately (for testing)."""
        logger.info("Running report job immediately...")
        self.job_function()
