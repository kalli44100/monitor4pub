"""Base chart functionality"""
import tkinter as tk
from typing import List, Optional
import logging
import math

logger = logging.getLogger(__name__)

class BaseChart(tk.Canvas):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.config(bg='white')
        
        # Chart dimensions
        self.margin_left = 50
        self.margin_right = 100
        self.margin_bottom = 40
        self.margin_top = 20
        
        # Chart state
        self.price_scale = None
        self.vertical_zoom = 1.0
        self.price_offset = 0.0
        self.zoom_start = None
        self.drag_start = None
        
        # Visual elements
        self.grid_lines = []
        self.price_labels = []
        self.time_labels = []
        
        # Bind events
        self.bind('<Button-1>', self.start_drag)
        self.bind('<B1-Motion>', self.handle_drag)
        self.bind('<ButtonRelease-1>', self.end_drag)
        self.bind('<Control-Button-1>', self.start_zoom)
        self.bind('<Control-B1-Motion>', self.handle_zoom)
        
        # Initialize empty chart
        self.after(100, self._initialize_after_map)
        
    def _initialize_after_map(self):
        """Initialize chart after widget is mapped"""
        height = self.winfo_height()
        if height > 1:
            self._draw_empty_grid()
        else:
            self.after(100, self._initialize_after_map)
            
    def _draw_empty_grid(self):
        """Draw empty chart grid"""
        width = self.winfo_width()
        height = self.winfo_height()
        
        # Clear previous grid
        for line in self.grid_lines:
            self.delete(line)
        self.grid_lines.clear()
        
        # Draw horizontal grid lines
        for i in range(5):
            y = i * (height - self.margin_bottom) / 4
            line = self.create_line(
                self.margin_left, y,
                width - self.margin_right, y,
                fill='lightgray',
                dash=(2, 2)
            )
            self.grid_lines.append(line)
            
        # Draw axes
        self.grid_lines.append(self.create_line(
            self.margin_left, height - self.margin_bottom,
            width - self.margin_right, height - self.margin_bottom,
            fill='black', width=1
        ))
        self.grid_lines.append(self.create_line(
            width - self.margin_right, self.margin_top,
            width - self.margin_right, height - self.margin_bottom,
            fill='black', width=1
        ))
        
    def _draw_price_scale(self, min_price: float, max_price: float):
        """Draw price scale on right side"""
        width = self.winfo_width()
        height = self.winfo_height()
        
        # Clear old labels
        for label in self.price_labels:
            self.delete(label)
        self.price_labels.clear()
        
        # Apply zoom and offset
        price_range = max_price - min_price
        center_price = (max_price + min_price) / 2
        zoomed_range = price_range * self.vertical_zoom
        
        min_price = center_price - (zoomed_range / 2) + self.price_offset
        max_price = center_price + (zoomed_range / 2) + self.price_offset
        
        # Draw price levels
        for i in range(5):
            y = self.margin_top + (i * (height - self.margin_top - self.margin_bottom) / 4)
            price = max_price - (i * (max_price - min_price) / 4)
            
            # Draw grid line
            self.create_line(
                self.margin_left, y,
                width - self.margin_right, y,
                fill='lightgray',
                dash=(2, 2)
            )
            
            # Draw price label
            label = self.create_text(
                width - self.margin_right + 50,
                y,
                text=f"${price:,.2f}",
                anchor='w',
                font=('Arial', 8),
                fill='black'
            )
            self.price_labels.append(label)
            
    def start_drag(self, event):
        """Start price scale drag"""
        width = self.winfo_width()
        if width - event.x <= self.margin_right:
            self.drag_start = event.y
            
    def handle_drag(self, event):
        """Handle price scale dragging"""
        if self.drag_start is not None:
            dy = event.y - self.drag_start
            self.price_offset += dy * self.vertical_zoom
            self.drag_start = event.y
            self.redraw()
            
    def end_drag(self, event):
        """End price scale drag"""
        self.drag_start = None
        
    def start_zoom(self, event):
        """Start zoom operation"""
        width = self.winfo_width()
        if width - event.x <= self.margin_right:
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
        """Redraw chart - to be implemented by subclasses"""
        pass