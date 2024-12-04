"""Market data utility functions"""

import math
import logging
from typing import Any, Optional
from ib_insync import IB, Ticker
import time

logger = logging.getLogger(__name__)


def is_valid_price(value: Any) -> bool:
    """Check if a price value is valid"""
    if value is None:
        return False
    try:
        float_val = float(value)
        return not (math.isnan(float_val) or float_val == 0)
    except (ValueError, TypeError):
        return False


def format_price(price: Any) -> str:
    """Format price for display"""
    if not is_valid_price(price):
        return "N/A"
    return f"{float(price):.2f}"


def get_price(ticker: Ticker) -> float:
    """Get best available price from ticker"""
    if is_valid_price(ticker.last):
        return ticker.last
    if is_valid_price(ticker.bid) and is_valid_price(ticker.ask):
        return (ticker.bid + ticker.ask) / 2
    if is_valid_price(ticker.close):
        return ticker.close
    return 0.0


def wait_for_market_data(ib: IB, ticker: Ticker, timeout: int = 5) -> bool:
    """Wait for market data with timeout"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        ib.sleep(0.2)
        if is_valid_price(ticker.last) or (
            is_valid_price(ticker.bid) and is_valid_price(ticker.ask)
        ):
            return True
    return False
