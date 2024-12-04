"""Unified chart component handling both price and options data"""

import tkinter as tk
from typing import List, Optional, Tuple
from datetime import datetime
import logging
import math

logger = logging.getLogger(__name__)


class UnifiedChart(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(bg="white")

        # Chart dimensions
        self.margin_left = 50
        self.margin_right = 100  # For price scale
        self.strike_margin = 60  # For strike prices
        self.margin_bottom = 40
        self.margin_top = 20

        # Data storage
        self.price_history = []
        self.current_bid = None
        self.current_ask = None
        self.options_data = None
        self.max_exposure = None
        self.exposure_type = "GFL"

        # Chart state
        self.price_scale = None
        self.vertical_zoom = 1.0
        self.horizontal_zoom = 1.0
        self.price_offset = 0.0
        self.zoom_start = None
        self.drag_start = None

        # Visual elements
        self.grid_lines = []
        self.price_labels = []
        self.time_labels = []
        self.price_lines = []
        self.current_price_line = None
        self.option_bars = []

        # Bind events
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.handle_drag)
        self.bind("<ButtonRelease-1>", self.end_drag)
        self.bind("<Control-Button-1>", self.start_zoom)
        self.bind("<Control-B1-Motion>", self.handle_zoom)
        self.bind("<Control-ButtonRelease-1>", self.end_zoom)

        # Initialize empty chart
        self.after(100, self.initialize_chart)

    def initialize_chart(self):
        """Initialize empty chart"""
        height = self.winfo_height()
        if height > 1:
            self._draw_empty_grid()
        else:
            self.after(100, self.initialize_chart)

    def _draw_empty_grid(self):
        """Draw empty chart grid"""
        width = self.winfo_width()
        height = self.winfo_height()

        # Clear previous grid
        for line in self.grid_lines:
            self.delete(line)
        self.grid_lines.clear()

        # Calculate usable area
        usable_width = width - self.margin_left - self.margin_right - self.strike_margin

        # Draw horizontal grid lines
        for i in range(5):
            y = self.margin_top + (
                i * (height - self.margin_top - self.margin_bottom) / 4
            )
            line = self.create_line(
                self.margin_left,
                y,
                self.margin_left + usable_width,
                y,
                fill="lightgray",
                dash=(2, 2),
            )
            self.grid_lines.append(line)

        # Draw axes
        self.grid_lines.append(
            self.create_line(
                self.margin_left,
                height - self.margin_bottom,
                self.margin_left + usable_width,
                height - self.margin_bottom,
                fill="black",
                width=1,
            )
        )
        self.grid_lines.append(
            self.create_line(
                self.margin_left + usable_width,
                self.margin_top,
                self.margin_left + usable_width,
                height - self.margin_bottom,
                fill="black",
                width=1,
            )
        )

    def update_prices(self, bid: float, ask: float):
        """Update current prices"""
        self.current_bid = bid
        self.current_ask = ask
        self.redraw()

    def update_history(self, bars: List):
        """Update price history"""
        self.price_history = bars

        # Calculate price scale from bid/ask
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
                self.price_scale = (
                    min_price - price_range * 0.1,
                    max_price + price_range * 0.1,
                )

        self.redraw()

    def update_options(
        self,
        data,
        max_exposure: float,
        spot_price: float = None,
        exposure_type: str = None,
    ):
        """Update options data"""
        self.options_data = data
        self.max_exposure = max_exposure
        if spot_price:
            self.current_bid = spot_price
            self.current_ask = spot_price
        if exposure_type:
            self.exposure_type = exposure_type

        self.redraw()

    def _calculate_exposure(self, ticker, exposure_type: str) -> float:
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
        elif exposure_type == "GFL" and self.current_bid:
            return delta * oi * self.current_bid  # GFlow's method
        else:  # "OI"
            return oi  # Open Interest only

    def redraw(self):
        """Redraw entire chart"""
        self.delete("all")  # Clear everything
        self._draw_empty_grid()

        if not self.price_history and not self.options_data:
            return

        # Draw price history if available
        if self.price_history and self.price_scale:
            self._draw_price_history()

        # Draw options data if available
        if self.options_data:
            self._draw_options_data()

        # Draw current price line and bid/ask
        if self.current_bid and self.current_ask:
            self._draw_current_price()

    def _draw_price_history(self):
        """Draw price history"""
        width = self.winfo_width()
        height = self.winfo_height()
        usable_width = width - self.margin_left - self.margin_right - self.strike_margin

        # Draw price scale
        self._draw_price_scale()

        # Draw bid/ask lines
        bid_points = []
        ask_points = []

        visible_bars = self._get_visible_bars()

        for i, bar in enumerate(visible_bars):
            x = self.margin_left + (usable_width * i / len(visible_bars))

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
            self.create_line(bid_points, fill="red", width=1, smooth=True)

        if len(ask_points) >= 4:
            self.create_line(ask_points, fill="green", width=1, smooth=True)

        # Draw current bid/ask labels
        if self.current_bid and self.current_ask:
            # Bid label
            self.create_text(
                width - self.margin_right - self.strike_margin + 5,
                self._price_to_y(self.current_bid),
                text=f"Bid: ${self.current_bid:.2f}",
                anchor="w",
                fill="red",
                font=("Arial", 8),
            )

            # Ask label
            self.create_text(
                width - self.margin_right - self.strike_margin + 5,
                self._price_to_y(self.current_ask),
                text=f"Ask: ${self.current_ask:.2f}",
                anchor="w",
                fill="green",
                font=("Arial", 8),
            )

        # Draw time axis
        self._draw_time_axis(visible_bars)

    def _get_visible_bars(self) -> List:
        """Get visible bars based on horizontal zoom"""
        if not self.price_history:
            return []

        total_bars = len(self.price_history)
        visible_bars = int(total_bars / self.horizontal_zoom)
        start_idx = max(0, total_bars - visible_bars)
        return self.price_history[start_idx:]

    def _draw_options_data(self):
        """Draw options data"""
        if not self.options_data or not self.max_exposure:
            return

        width = self.winfo_width()
        height = self.winfo_height()
        usable_height = height - self.margin_top - self.margin_bottom
        bar_height = usable_height / (len(self.options_data) + 1)
        bar_thickness = bar_height * 0.25

        # Calculate exposures and normalize to percentages
        exposures = []
        max_exp = 0

        for strike, call_ticker, put_ticker in self.options_data:
            call_exp = self._calculate_exposure(call_ticker, self.exposure_type)
            put_exp = self._calculate_exposure(put_ticker, self.exposure_type)
            max_exp = max(max_exp, call_exp, put_exp)
            exposures.append((strike, call_exp, put_exp))

        # Draw bars
        for i, (strike, call_exp, put_exp) in enumerate(exposures):
            y = self._price_to_y(strike)  # Align with price scale

            # Calculate bar widths as percentages
            call_width = (call_exp / max_exp) * (
                width - self.margin_left - self.margin_right - self.strike_margin
            )
            put_width = (put_exp / max_exp) * (
                width - self.margin_left - self.margin_right - self.strike_margin
            )

            # Draw call exposure (green)
            if call_exp > 0:
                self.create_rectangle(
                    width - self.margin_right - self.strike_margin,
                    y - bar_thickness,
                    width - self.margin_right - self.strike_margin - call_width,
                    y,
                    fill="#90EE90",
                    outline="",
                )

            # Draw put exposure (red)
            if put_exp > 0:
                self.create_rectangle(
                    width - self.margin_right - self.strike_margin,
                    y,
                    width - self.margin_right - self.strike_margin - put_width,
                    y + bar_thickness,
                    fill="#FFB6C6",
                    outline="",
                )

            # Draw strike price
            self.create_text(
                width - self.margin_right + 10,
                y,
                text=str(strike),
                anchor="w",
                fill="black",
            )

    def _draw_current_price(self):
        """Draw current price line"""
        width = self.winfo_width()
        mid_price = (self.current_bid + self.current_ask) / 2
        y = self._price_to_y(mid_price)

        self.create_line(
            self.margin_left,
            y,
            width - self.margin_right - self.strike_margin,
            y,
            fill="blue",
            width=1,
            dash=(4, 4),
        )

    def _draw_price_scale(self):
        """Draw price scale"""
        if not self.price_scale:
            return

        width = self.winfo_width()
        height = self.winfo_height()
        min_price, max_price = self.price_scale

        # Apply zoom and offset
        price_range = max_price - min_price
        center_price = (max_price + min_price) / 2
        zoomed_range = price_range * self.vertical_zoom

        min_price = center_price - (zoomed_range / 2) + self.price_offset
        max_price = center_price + (zoomed_range / 2) + self.price_offset

        # Draw price levels
        for i in range(5):
            price = max_price - (i * (max_price - min_price) / 4)
            y = self._price_to_y(price)

            # Draw grid line
            self.create_line(
                self.margin_left,
                y,
                width - self.margin_right - self.strike_margin,
                y,
                fill="lightgray",
                dash=(2, 2),
            )

            # Draw price label
            self.create_text(
                width - self.margin_right - self.strike_margin + 25,
                y,
                text=f"${price:,.2f}",
                anchor="w",
                font=("Arial", 8),
                fill="black",
            )

    def _draw_time_axis(self, bars: List):
        """Draw time axis"""
        if not bars:
            return

        width = self.winfo_width()
        height = self.winfo_height()
        usable_width = width - self.margin_left - self.margin_right - self.strike_margin

        # Draw time labels
        num_labels = 5
        step = max(1, len(bars) // (num_labels - 1))

        for i in range(0, len(bars), step):
            if i >= len(bars):
                break

            bar = bars[i]
            x = self.margin_left + (usable_width * i / len(bars))

            self.create_text(
                x,
                height - self.margin_bottom + 20,
                text=bar.date.strftime("%H:%M:%S"),
                anchor="n",
                font=("Arial", 8),
                fill="black",
            )

    def _price_to_y(self, price: float) -> float:
        """Convert price to y coordinate"""
        if not self.price_scale:
            return 0

        min_price, max_price = self.price_scale
        height = self.winfo_height()
        usable_height = height - self.margin_top - self.margin_bottom

        # Apply zoom and offset
        price_range = max_price - min_price
        center_price = (max_price + min_price) / 2
        zoomed_range = price_range * self.vertical_zoom

        min_price = center_price - (zoomed_range / 2) + self.price_offset
        max_price = center_price + (zoomed_range / 2) + self.price_offset

        return self.margin_top + (
            (max_price - price) * usable_height / (max_price - min_price)
        )

    def start_drag(self, event):
        """Start price scale drag"""
        width = self.winfo_width()
        height = self.winfo_height()

        if (
            width - event.x <= self.margin_right + self.strike_margin
        ):  # Right margin - price scale
            self.drag_start = (event.x, event.y, "price")
        elif event.y > height - self.margin_bottom:  # Bottom margin - time scale
            self.drag_start = (event.x, event.y, "time")

    def handle_drag(self, event):
        """Handle dragging"""
        if not self.drag_start:
            return

        x, y, drag_type = self.drag_start

        if drag_type == "price":
            dy = (event.y - y) * 0.05  # Reduced sensitivity
            self.price_offset += dy * self.vertical_zoom
            self.drag_start = (x, event.y, drag_type)
        elif drag_type == "time":
            dx = event.x - x
            self.horizontal_zoom = max(1.0, self.horizontal_zoom + dx * 0.01)
            self.drag_start = (event.x, y, drag_type)

        self.redraw()

    def end_drag(self, event):
        """End drag operation"""
        self.drag_start = None

    def start_zoom(self, event):
        """Start zoom operation"""
        width = self.winfo_width()
        height = self.winfo_height()

        if (
            width - event.x <= self.margin_right + self.strike_margin
        ):  # Right margin - price zoom
            self.zoom_start = (event.x, event.y, "price")
        elif event.y > height - self.margin_bottom:  # Bottom margin - time zoom
            self.zoom_start = (event.x, event.y, "time")

    def handle_zoom(self, event):
        """Handle zoom dragging"""
        if not self.zoom_start:
            return

        x, y, zoom_type = self.zoom_start

        if zoom_type == "price":
            dy = event.y - y
            zoom_factor = math.exp(-dy / 200)
            self.vertical_zoom *= zoom_factor
            self.vertical_zoom = max(0.1, min(10.0, self.vertical_zoom))
        elif zoom_type == "time":
            dx = event.x - x
            zoom_factor = math.exp(dx / 200)
            self.horizontal_zoom *= zoom_factor
            self.horizontal_zoom = max(0.1, min(10.0, self.horizontal_zoom))

        self.zoom_start = (event.x, event.y, zoom_type)
        self.redraw()

    def end_zoom(self, event):
        """End zoom operation"""
        self.zoom_start = None
