"""Price chart component"""

from typing import List, Optional
from datetime import datetime
import logging
from .base_chart import BaseChart

logger = logging.getLogger(__name__)


class PriceChart(BaseChart):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # Price data
        self.price_history = []
        self.current_bid = None
        self.current_ask = None

        # Visual elements
        self.price_lines = []
        self.current_price_line = None

    def update_prices(self, bid: float, ask: float):
        """Update current prices"""
        self.current_bid = bid
        self.current_ask = ask
        self.redraw()

    def update_history(self, bars: List):
        """Update price history"""
        self.price_history = bars

        # Calculate initial scale
        if bars:
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
                self.price_scale = (min_price, max_price + price_range * 0.1)

        self.redraw()

    def redraw(self):
        """Redraw price chart"""
        if not self.price_history:
            return

        # Clear previous elements
        for line in self.price_lines:
            self.delete(line)
        self.price_lines.clear()

        if self.current_price_line:
            self.delete(self.current_price_line)

        # Get dimensions
        width = self.winfo_width()
        height = self.winfo_height()
        usable_width = width - self.margin_left - self.margin_right
        usable_height = height - self.margin_top - self.margin_bottom

        # Draw price scale
        if self.price_scale:
            self._draw_price_scale(*self.price_scale)

        # Draw bid/ask lines
        bid_points = []
        ask_points = []

        for i, bar in enumerate(self.price_history):
            x = self.margin_left + (usable_width * i / len(self.price_history))

            if hasattr(bar, "bid") and hasattr(bar, "ask"):
                y_bid = self._price_to_y(bar.bid)
                y_ask = self._price_to_y(bar.ask)
                bid_points.extend([x, y_bid])
                ask_points.extend([x, y_ask])
            else:
                y = self._price_to_y(bar.close)
                bid_points.extend([x, y])
                ask_points.extend([x, y])

        # Draw lines
        if len(bid_points) >= 4:
            line = self.create_line(bid_points, fill="green", width=1, smooth=True)
            self.price_lines.append(line)

        if len(ask_points) >= 4:
            line = self.create_line(ask_points, fill="red", width=1, smooth=True)
            self.price_lines.append(line)

        # Draw current price line
        if self.current_bid and self.current_ask:
            mid_price = (self.current_bid + self.current_ask) / 2
            y = self._price_to_y(mid_price)

            self.current_price_line = self.create_line(
                self.margin_left,
                y,
                width - self.margin_right,
                y,
                fill="blue",
                width=1,
                dash=(4, 4),
            )

        # Update time axis
        self._draw_time_axis()

    def _price_to_y(self, price: float) -> float:
        """Convert price to y coordinate"""
        if not self.price_scale:
            return 0

        min_price, max_price = self.price_scale
        height = self.winfo_height()
        usable_height = height - self.margin_top - self.margin_bottom

        # Apply zoom and offset
        price_range = max_price - min_price
        scaled_price = (price - min_price) / price_range

        return self.margin_top + (1 - scaled_price) * usable_height

    def _draw_time_axis(self):
        """Draw time axis with labels"""
        if not self.price_history:
            return

        # Clear old labels
        for label in self.time_labels:
            self.delete(label)
        self.time_labels.clear()

        # Draw time labels
        width = self.winfo_width()
        height = self.winfo_height()
        usable_width = width - self.margin_left - self.margin_right

        num_labels = 5
        step = max(1, len(self.price_history) // (num_labels - 1))

        for i in range(0, len(self.price_history), step):
            if i >= len(self.price_history):
                break

            bar = self.price_history[i]
            x = self.margin_left + (usable_width * i / len(self.price_history))

            label = self.create_text(
                x,
                height - self.margin_bottom + 20,
                text=bar.date.strftime("%H:%M:%S"),
                anchor="n",
                font=("Arial", 8),
                fill="black",
            )
            self.time_labels.append(label)
