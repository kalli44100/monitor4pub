"""Chart management and updates"""

import logging
from typing import List, Optional
from datetime import datetime
from .options_chart import OptionsChart

logger = logging.getLogger(__name__)


class ChartManager:
    def __init__(self, chart: OptionsChart):
        self.chart = chart
        self.historical_bars = None
        self.current_data = None
        self.max_exposure = None
        self.spot_price = None

        # Initialize empty chart
        self.chart.after(100, self.initialize_chart)

    def initialize_chart(self):
        """Initialize empty chart"""
        height = self.chart.winfo_height()
        if height > 1:
            self.chart._draw_empty_grid()
        else:
            self.chart.after(100, self.initialize_chart)

    def update_prices(self, bid: float, ask: float):
        """Handle real-time price updates"""
        if not self.historical_bars:
            return

        # Update last bar with new prices
        last_bar = self.historical_bars[-1]
        last_bar.bid = bid
        last_bar.ask = ask

        # Update spot price
        self.spot_price = (bid + ask) / 2

        # Redraw chart
        self.chart.draw_price_history(self.historical_bars, self.chart.price_scale)
        self.chart.draw_price_line(self.spot_price)

    def update_with_historical(self, bars: List):
        """Update chart with historical data"""
        if not bars:
            return

        self.historical_bars = bars

        # Calculate price range from bid/ask
        prices = []
        for bar in bars:
            if hasattr(bar, "bid") and hasattr(bar, "ask"):
                prices.extend([bar.bid, bar.ask])
            else:
                prices.append(bar.close)

        if prices:
            min_price = min(prices)
            max_price = max(prices)
            price_range = max_price - min_price
            scale = max_price + (price_range * 0.1)  # Add 10% margin

            # Get current price from most recent bar
            last_bar = bars[-1]
            self.spot_price = (
                (last_bar.bid + last_bar.ask) / 2
                if hasattr(last_bar, "bid")
                else last_bar.close
            )

            # Draw historical data
            self.chart.draw_price_history(bars, scale)

            # Draw current price line
            if self.spot_price:
                self.chart.draw_price_line(self.spot_price)

    def update_with_options(self, delta_data, max_exposure, spot_price):
        """Update chart with options data"""
        self.current_data = delta_data
        self.max_exposure = max_exposure
        self.spot_price = spot_price

        # Store historical data
        if self.historical_bars:
            self.chart.historical_bars = self.historical_bars

        # Draw options data
        self.chart.draw_delta_chart(
            delta_data,
            max_exposure,
            spot_price=spot_price,
            exposure_type=self.chart.exposure_type,
        )

    def update_exposure_type(self, exposure_type: str):
        """Update exposure calculation type"""
        if self.current_data:
            self.chart.draw_delta_chart(
                self.current_data,
                self.max_exposure,
                spot_price=self.spot_price,
                exposure_type=exposure_type,
            )
