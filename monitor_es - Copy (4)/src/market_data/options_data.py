"""Options market data processing"""

from datetime import datetime
from typing import List, Tuple, Optional
from ib_insync import IB, Ticker, Contract
import logging
from .utils import is_valid_price

logger = logging.getLogger(__name__)


class OptionsDataProcessor:
    def __init__(self, ib: IB):
        self.ib = ib
        self.market_data_subscriptions: List[Ticker] = []
        self.spot_price: Optional[float] = None

    def cleanup(self):
        """Clean up market data subscriptions"""
        try:
            if self.ib.isConnected():
                for subscription in self.market_data_subscriptions:
                    try:
                        self.ib.cancelMktData(subscription)
                    except:
                        pass
                self.market_data_subscriptions.clear()
        except Exception as e:
            logger.error(f"Error cleaning up market data: {str(e)}")

    def calculate_exposure(self, ticker: Ticker, exposure_type: str) -> float:
        """Calculate exposure based on type"""
        if not ticker or not hasattr(ticker, "modelGreeks") or not ticker.modelGreeks:
            return 0.0

        # Get base values
        delta = abs(ticker.modelGreeks.delta) if ticker.modelGreeks.delta else 0.0
        volume = ticker.volume if hasattr(ticker, "volume") and ticker.volume else 0.0

        # Get open interest based on option type
        if ticker.contract.right == "C":
            oi = ticker.callOpenInterest if hasattr(ticker, "callOpenInterest") else 0.0
        else:
            oi = ticker.putOpenInterest if hasattr(ticker, "putOpenInterest") else 0.0

        # Calculate exposure based on type
        if exposure_type == "DEX":
            return delta * oi * 50  # Delta Exposure
        elif exposure_type == "VOI":
            return volume * oi  # Volume-OI
        elif exposure_type == "GFL" and self.spot_price:
            return delta * oi * self.spot_price  # GFlow's method
        else:  # "OI"
            return oi  # Open Interest only

    def request_market_data(
        self,
        contracts: List[Tuple[float, Contract, Contract]],
        spot_price: Optional[float] = None,
    ) -> List[Tuple[float, Ticker, Ticker]]:
        """Request market data for option contracts"""
        self.spot_price = spot_price
        tickers = []
        genericTickList = "100,101,104,106,236,258"

        for strike, call, put in contracts:
            call_ticker = self.ib.reqMktData(call, genericTickList)
            put_ticker = self.ib.reqMktData(put, genericTickList)
            tickers.append((strike, call_ticker, put_ticker))
            self.market_data_subscriptions.extend([call_ticker, put_ticker])

        return tickers

    def process_market_data(
        self, tickers: List[Tuple[float, Ticker, Ticker]], exposure_type: str = "DEX"
    ) -> Tuple[List[Tuple[float, Ticker, Ticker]], float]:
        """Process market data and calculate exposures"""
        self.ib.sleep(5)  # Wait for data

        delta_data = []
        max_exposure = 0

        for strike, call_ticker, put_ticker in tickers:
            try:
                delta_data.append((strike, call_ticker, put_ticker))

                call_exposure = self.calculate_exposure(call_ticker, exposure_type)
                put_exposure = self.calculate_exposure(put_ticker, exposure_type)

                max_exposure = max(max_exposure, call_exposure, put_exposure)

                logger.info(
                    f"Strike {strike} - Call Exposure: {call_exposure:.2f}, "
                    f"Put Exposure: {put_exposure:.2f}"
                )

            except Exception as e:
                logger.error(f"Error processing data for strike {strike}: {str(e)}")
                continue

        return delta_data, max(max_exposure, 1.0)
