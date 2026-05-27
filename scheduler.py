"""
APScheduler job: retrain the ML model every Saturday at 12:00 noon.
This runs as a background thread when the FastAPI app starts.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

def retrain_job():
    """Called automatically every Saturday at noon."""
    logger.info("[scheduler] Starting scheduled retraining...")
    try:
        from machine_learning.machine_learning import train_model
        train_model()
        logger.info("[scheduler] Retraining complete ✓")
    except Exception as e:
        logger.error(f"[scheduler] Retraining failed: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        retrain_job,
        trigger=CronTrigger(day_of_week="sat", hour=12, minute=0),
        id="weekly_retrain",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[scheduler] Weekly retraining scheduler started (Sat 12:00) ✓")
    return scheduler