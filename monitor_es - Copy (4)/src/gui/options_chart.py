"""Options chart visualization component"""

import tkinter as tk
from typing import List, Tuple, Optional
from datetime import datetime
import logging
import math

logger = logging.getLogger(__name__)


class OptionsChart(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(bg="white")

        # Store current data
        self.current_data = None
        self.current_max = None
        self.current_spot = None
        self.exposure_type = "GFL"  # Default to GFlow's method
        self.historical_bars = None
        self.price_scale = None

        # Chart state
        self.price_scale_labels = []
        self.time_labels = []
        self.option_bars = []
        self.grid_lines = []
        self.price_line = None
        self.price_history_lines = []
        self.vertical_zoom = 1.0
        self.price_offset = 0.0
        self.zoom_start = None
        self.drag_start = None

        # Bind mouse events
        self.bind("<Button-1>", self.start_drag)
        self.bind("<B1-Motion>", self.handle_drag)
        self.bind("<ButtonRelease-1>", self.end_drag)
        self.bind("<Control-Button-1>", self.start_zoom)
        self.bind("<Control-B1-Motion>", self.handle_zoom)

        # Initialize empty chart
        self.after(100, self._initialize_after_map)

    def _initialize_after_map(self):
        """Initialize chart after widget is mapped"""
        height = self.winfo_height()
        if height > 1:  # Ensure widget has size
            self._draw_empty_grid()
        else:
            self.after(100, self._initialize_after_map)

    def _draw_empty_grid(self):
        """Draw empty chart grid"""
        width = self.winfo_width()
        height = self.winfo_height()
        margin_right = 100
        margin_bottom = 40

        # Clear previous grid
        for line in self.grid_lines:
            self.delete(line)
        self.grid_lines.clear()

        # Draw horizontal grid lines
        for i in range(5):
            y = i * (height - margin_bottom) / 4
            line = self.create_line(
                0, y, width - margin_right, y, fill="lightgray", dash=(2, 2)
            )
            self.grid_lines.append(line)

        # Draw axes
        self.grid_lines.append(
            self.create_line(
                0,
                height - margin_bottom,
                width - margin_right,
                height - margin_bottom,
                fill="black",
                width=1,
            )
        )
        self.grid_lines.append(
            self.create_line(
                width - margin_right,
                0,
                width - margin_right,
                height - margin_bottom,
                fill="black",
                width=1,
            )
        )

    def draw_price_history(self, bars: List, y_scale: float):
        """Draw price history from bars"""
        try:
            self.historical_bars = bars
            self.price_scale = y_scale

            # Clear old lines and labels
            self._clear_price_history()

            if not bars:
                return

            # Calculate dimensions
            width = self.winfo_width()
            height = self.winfo_height()
            margin_right = 100
            margin_left = 50
            margin_bottom = 40
            usable_width = width - margin_right - margin_left

            # Apply zoom to scale
            y_scale = y_scale / self.vertical_zoom

            # Draw price scale
            self._draw_price_scale(y_scale)

            # Draw bid/ask lines
            bid_points = []
            ask_points = []

            for i, bar in enumerate(bars):
                x = margin_left + (usable_width * i / len(bars))

                if hasattr(bar, "bid") and hasattr(bar, "ask"):
                    y_bid = self._price_to_y(bar.bid, y_scale)
                    y_ask = self._price_to_y(bar.ask, y_scale)
                    bid_points.extend([x, y_bid])
                    ask_points.extend([x, y_ask])
                else:
                    y = self._price_to_y(bar.close, y_scale)
                    bid_points.extend([x, y])
                    ask_points.extend([x, y])

            # Draw lines
            if len(bid_points) >= 4:
                bid_line = self.create_line(
                    bid_points, fill="green", width=1, smooth=True
                )
                self.price_history_lines.append(bid_line)

            if len(ask_points) >= 4:
                ask_line = self.create_line(
                    ask_points, fill="red", width=1, smooth=True
                )
                self.price_history_lines.append(ask_line)

            # Update time axis
            self._draw_time_axis(bars)

        except Exception as e:
            logger.error(f"Error drawing price history: {str(e)}")

    def _draw_price_scale(self, y_scale: float):
        """Draw price scale on right side"""
        width = self.winfo_width()
        height = self.winfo_height()
        margin_bottom = 40
        margin_right = 100

        # Clear old scale
        for label in self.price_scale_labels:
            self.delete(label)
        self.price_scale_labels.clear()

        # Calculate price range
        price_range = y_scale
        base_price = y_scale * self.price_offset / height

        # Draw price levels
        for i in range(5):
            y = i * (height - margin_bottom) / 4
            price = y_scale - (i * price_range / 4) + base_price

            # Draw price label
            label_id = self.create_text(
                width - margin_right + 50,
                y,
                text=f"${price:,.2f}",
                anchor="w",
                font=("Arial", 8),
                fill="black",
            )
            self.price_scale_labels.append(label_id)

    def draw_price_line(self, price: float):
        """Draw current price line"""
        if self.price_line:
            self.delete(self.price_line)

        if not self.price_scale:
            return

        width = self.winfo_width()
        margin_right = 100

        # Calculate y position
        y = self._price_to_y(price, self.price_scale / self.vertical_zoom)

        # Draw horizontal line
        self.price_line = self.create_line(
            0, y, width - margin_right, y, fill="blue", width=1, dash=(4, 4)
        )

    def _price_to_y(self, price: float, y_scale: float) -> float:
        """Convert price to y coordinate"""
        height = self.winfo_height()
        margin_bottom = 40
        usable_height = height - margin_bottom
        return (
            margin_bottom
            + ((y_scale - price) * usable_height / y_scale)
            + self.price_offset
        )

    def _draw_time_axis(self, bars: List):
        """Draw time axis with labels"""
        # Clear old labels
        for label in self.time_labels:
            self.delete(label)
        self.time_labels.clear()

        if not bars:
            return

        # Draw time labels
        width = self.winfo_width()
        height = self.winfo_height()
        margin_left = 50
        margin_right = 100
        margin_bottom = 40
        y = height - margin_bottom + 20
        num_labels = 5
        step = max(1, len(bars) // (num_labels - 1))

        for i in range(0, len(bars), step):
            if i >= len(bars):
                break

            time = bars[i].date
            x = margin_left + (
                (width - margin_left - margin_right) * i / (len(bars) - 1)
            )

            label_id = self.create_text(
                x,
                y,
                text=time.strftime("%H:%M:%S"),
                anchor="n",
                font=("Arial", 8),
                fill="black",
            )
            self.time_labels.append(label_id)

    def draw_delta_chart(self, data, max_exposure, spot_price=None, exposure_type=None):
        """Draw the options delta chart"""
        # Store current data
        self.current_data = data
        self.current_max = max_exposure
        self.current_spot = spot_price

        if exposure_type:
            self.exposure_type = exposure_type

        # Clear previous options data
        self._clear_options_data()

        # Calculate exposures
        exposures = []
        max_exp = 0

        for strike, call_ticker, put_ticker in data:
            call_exp = self._calculate_exposure(call_ticker, self.exposure_type)
            put_exp = self._calculate_exposure(put_ticker, self.exposure_type)
            max_exp = max(max_exp, call_exp, put_exp)
            exposures.append((strike, call_exp, put_exp))

        # Ensure non-zero scale
        max_exp = max(max_exp, 1.0)

        # Chart dimensions
        width = self.winfo_width()
        height = self.winfo_height()
        margin_right = 100
        margin_bottom = 40
        axis_x = width - margin_right
        bar_max_width = width - margin_right - 50
        bar_height = (
            (height - margin_bottom) / (len(data) + 1)
            if data
            else (height - margin_bottom) / 10
        )
        bar_thickness = bar_height * 0.25

        # Draw strikes and exposure bars
        for i, (strike, call_exp, put_exp) in enumerate(exposures):
            y = (i + 1) * bar_height

            # Calculate bar widths
            call_width = (call_exp / max_exp) * bar_max_width if max_exp > 0 else 0
            put_width = (put_exp / max_exp) * bar_max_width if max_exp > 0 else 0

            # Draw call exposure (green)
            if call_exp > 0:
                bar = self.create_rectangle(
                    axis_x,
                    y - bar_thickness,
                    axis_x - call_width,
                    y,
                    fill="#90EE90",
                    outline="",
                )
                self.option_bars.append(bar)

            # Draw put exposure (red)
            if put_exp > 0:
                bar = self.create_rectangle(
                    axis_x,
                    y,
                    axis_x - put_width,
                    y + bar_thickness,
                    fill="#FFB6C6",
                    outline="",
                )
                self.option_bars.append(bar)

            # Draw strike price
            text = self.create_text(
                width - 5, y, text=str(strike), anchor="e", fill="black"
            )
            self.option_bars.append(text)

        # Draw exposure scale
        self._draw_exposure_scale(max_exp)

        # Redraw price history if available
        if self.historical_bars and self.price_scale:
            self.draw_price_history(self.historical_bars, self.price_scale)

        # Draw current price line
        if spot_price:
            self.draw_price_line(spot_price)

    def _calculate_exposure(self, ticker, exposure_type: str) -> float:
        """Calculate exposure based on type"""
        if not ticker or not hasattr(ticker, "modelGreeks") or not ticker.modelGreeks:
            return 0.0

        # Get base values
        delta = abs(ticker.modelGreeks.delta) if ticker.modelGreeks.delta else 0.0
        oi = ticker.openInterest if hasattr(ticker, "openInterest") else 0.0
        volume = ticker.volume if hasattr(ticker, "volume") else 0.0

        # Calculate exposure based on type
        if exposure_type == "DEX":
            return delta * oi * 50  # Delta * OI * Contract Multiplier
        elif exposure_type == "VOI":
            return volume * oi  # Volume * OI
        elif exposure_type == "OI":
            return oi  # Just OI
        elif exposure_type == "GFL" and self.current_spot:
            return delta * oi * self.current_spot  # Delta * OI * Spot Price
        return 0.0

    def _draw_exposure_scale(self, max_exp: float):
        """Draw exposure scale"""
        width = self.winfo_width()
        height = self.winfo_height()
        margin_right = 100
        margin_bottom = 40
        axis_x = width - margin_right
        bar_max_width = width - margin_right - 50

        # Draw scale points
        scale_y = height - margin_bottom + 10
        scale_points = [0, max_exp / 4, max_exp / 2, (3 * max_exp) / 4, max_exp]

        for i, exposure in enumerate(scale_points):
            x = axis_x - (i * bar_max_width / 4)
            label = self.create_text(
                x,
                scale_y,
                text=f"{exposure:,.0f}",
                fill="black",
                anchor="n",
                font=("Arial", 8),
            )
            self.option_bars.append(label)

    def _clear_price_history(self):
        """Clear price history elements"""
        for line in self.price_history_lines:
            self.delete(line)
        self.price_history_lines.clear()

        for label in self.price_scale_labels:
            self.delete(label)
        self.price_scale_labels.clear()

        for label in self.time_labels:
            self.delete(label)
        self.time_labels.clear()

    def _clear_options_data(self):
        """Clear options data elements"""
        for bar in self.option_bars:
            self.delete(bar)
        self.option_bars.clear()

    def start_drag(self, event):
        """Start price scale drag"""
        width = self.winfo_width()
        if width - event.x <= 100:  # Right margin
            self.drag_start = event.y

    def handle_drag(self, event):
        """Handle price scale dragging"""
        if self.drag_start is not None:
            dy = event.y - self.drag_start
            self.price_offset += dy
            self.drag_start = event.y
            self.redraw()

    def end_drag(self, event):
        """End price scale drag"""
        self.drag_start = None

    def start_zoom(self, event):
        """Start zoom operation"""
        width = self.winfo_width()
        if width - event.x <= 100:  # Right margin
            self.zoom_start = event.y

    def handle_zoom(self, event):
        """Handle zoom dragging"""
        if self.zoom_start is not None:
            dy = event.y - self.zoom_start
            zoom_factor = math.exp(-dy / 200)
            self.vertical_zoom *= zoom_factor
            self.vertical_zoom = max(0.1, min(10.0, self.vertical_zoom))
            self.zoom_start = event.y
            self.redraw()

    def redraw(self):
        """Redraw chart with current data"""
        if self.historical_bars and self.price_scale:
            self.draw_price_history(self.historical_bars, self.price_scale)

        if self.current_data:
            self.draw_delta_chart(
                self.current_data,
                self.current_max,
                self.current_spot,
                self.exposure_type,
            )
