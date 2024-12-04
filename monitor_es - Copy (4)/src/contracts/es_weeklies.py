"""ES Weekly Options Trading Class Management"""

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def get_weekly_trading_class() -> str:
    """
    Get the current ES weekly options trading class.
    Hardcoded to E1B as we know this is correct.
    """
    return "E1B"  # Current trading class


def get_next_expiry() -> datetime:
    """Get next weekly options expiration"""
    today = datetime.now().date()
    days_to_friday = (4 - today.weekday()) % 7
    next_friday = today + timedelta(days=days_to_friday)
    return next_friday
