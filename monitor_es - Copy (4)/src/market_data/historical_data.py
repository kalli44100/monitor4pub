"""Historical market data utilities"""

from ib_insync import IB, Future
import logging
from typing import List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def request_historical_data(
    ib: IB,
    contract: Future,
    duration: str = "1 D",
    bar_size: str = "1 min",
    what_to_show: str = "BID_ASK",  # Changed default to BID_ASK
    use_rth: bool = True,
) -> Optional[List]:
    """
    Request historical price data for a contract
    """
    try:
        # Request historical data
        bars = ib.reqHistoricalData(
            contract,
            endDateTime="",
            durationStr=duration,
            barSizeSetting=bar_size,
            whatToShow=what_to_show,
            useRTH=use_rth,
            formatDate=1,
        )

        if bars:
            logger.info(f"Retrieved {len(bars)} historical bars")
            # Log first bar for debugging
            if len(bars) > 0:
                first_bar = bars[0]
                logger.info(
                    f"First bar data: bid={first_bar.bid if hasattr(first_bar, 'bid') else 'N/A'}, "
                    f"ask={first_bar.ask if hasattr(first_bar, 'ask') else 'N/A'}, "
                    f"close={first_bar.close}"
                )

        return bars

    except Exception as e:
        logger.error(f"Error requesting historical data: {str(e)}")
        return None
