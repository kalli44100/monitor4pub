"""ES Futures market data handling"""

from ib_insync import IB, Future
import logging
from typing import Optional, List, Tuple
from datetime import datetime
from .historical_data import request_historical_data

logger = logging.getLogger(__name__)


class ESFuturesData:
    def __init__(self, ib: IB):
        self.ib = ib
        self.contract = None
        self.ticker = None
        self.price_callbacks = []

    def initialize_contract(self) -> bool:
        """Initialize ES futures contract"""
        try:
            self.contract = Future(
                symbol="ES",
                lastTradeDateOrContractMonth="20241220",
                exchange="CME",
                currency="USD",
                localSymbol="ESZ4",
            )

            qualified = self.ib.qualifyContracts(self.contract)
            if not qualified:
                logger.error("Could not qualify ES futures contract")
                return False

            self.contract = qualified[0]
            return True

        except Exception as e:
            logger.error(f"Error initializing ES contract: {str(e)}")
            return False

    def start_market_data(self) -> bool:
        """Start real-time market data subscription"""
        try:
            if not self.contract:
                return False

            genericTickList = "100,101,104,106,236,258"
            self.ticker = self.ib.reqMktData(self.contract, genericTickList)

            # Set up price update callback
            self.ticker.updateEvent += self.on_price_update
            return True

        except Exception as e:
            logger.error(f"Error starting market data: {str(e)}")
            return False

    def on_price_update(self, ticker):
        """Handle price updates"""
        try:
            if hasattr(ticker, "bid") and hasattr(ticker, "ask"):
                for callback in self.price_callbacks:
                    callback(ticker.bid, ticker.ask)
        except Exception as e:
            logger.error(f"Error handling price update: {str(e)}")

    def add_price_callback(self, callback):
        """Add price update callback"""
        self.price_callbacks.append(callback)

    def get_historical_data(self, duration: str = "1 D", bar_size: str = "1 min"):
        """Get historical price data"""
        if not self.contract:
            return None

        return request_historical_data(
            self.ib,
            self.contract,
            duration=duration,
            bar_size=bar_size,
            what_to_show="BID_ASK",
        )

    def cleanup(self):
        """Clean up market data subscriptions"""
        if self.ticker:
            self.ticker.updateEvent -= self.on_price_update
            self.ib.cancelMktData(self.ticker)
            self.ticker = None
