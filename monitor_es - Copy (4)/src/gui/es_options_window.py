"""ES Options Monitor GUI Window"""

import tkinter as tk
from tkinter import ttk
from .unified_chart import UnifiedChart
import logging

logger = logging.getLogger(__name__)


class ESOptionsWindow:
    def __init__(self, on_refresh, on_cancel, on_connect):
        self.root = tk.Tk()
        self.root.title("ES Options Monitor")
        self.root.geometry("1400x900")

        # Create chart first
        self.chart = UnifiedChart(self.root, width=1400, height=750)
        self.chart.pack(fill="both", expand=True, padx=10, pady=5)

        # Create control panel
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=5)

        # Add exposure type dropdown
        exposure_frame = tk.Frame(button_frame)
        exposure_frame.pack(side="right", padx=20)

        tk.Label(exposure_frame, text="Exposure Type:").pack(side="left", padx=5)
        self.exposure_type = tk.StringVar(value="GFL")
        self.exposure_dropdown = ttk.Combobox(
            exposure_frame,
            textvariable=self.exposure_type,
            values=["DEX", "VOI", "OI", "GFL"],
            state="readonly",
            width=10,
        )
        self.exposure_dropdown.pack(side="left")
        self.exposure_dropdown.bind("<<ComboboxSelected>>", self._on_exposure_changed)

        # Add buttons
        self.refresh_btn = tk.Button(
            button_frame,
            text="Refresh Options",
            command=on_refresh,
            width=20,
            height=2,
        )
        self.refresh_btn.pack(side="left", padx=5)

        self.cancel_btn = tk.Button(
            button_frame,
            text="Cancel Refresh",
            command=on_cancel,
            width=20,
            height=2,
            state="disabled",
        )
        self.cancel_btn.pack(side="left", padx=5)

        self.connect_btn = tk.Button(
            button_frame,
            text="Connect",
            command=on_connect,
            width=20,
            height=2,
        )
        self.connect_btn.pack(side="left", padx=5)

        self.conn_status = tk.Label(
            button_frame, text="Not Connected", font=("Arial", 12), fg="red"
        )
        self.conn_status.pack(side="left", padx=20)

    def _on_exposure_changed(self, event):
        """Handle exposure type change"""
        self.chart.update_options(
            self.chart.options_data,
            self.chart.max_exposure,
            self.chart.current_bid,
            exposure_type=self.exposure_type.get(),
        )

    def update_connection_status(self, connected, error_msg=None):
        """Update connection status display"""
        if connected:
            self.conn_status.config(text="Connected", fg="green")
            self.connect_btn.config(text="Disconnect")
        else:
            text = "Disconnected" if not error_msg else f"Error: {error_msg}"
            self.conn_status.config(text=text, fg="red")
            self.connect_btn.config(text="Connect")

    def set_refresh_state(self, is_refreshing):
        """Update refresh button states"""
        if is_refreshing:
            self.refresh_btn.config(state="disabled")
            self.cancel_btn.config(state="normal")
        else:
            self.refresh_btn.config(state="normal")
            self.cancel_btn.config(state="disabled")

    def update_chart(self, delta_data, max_exposure, spot_price=None):
        """Update the options chart"""
        self.chart.update_options(
            delta_data, max_exposure, spot_price, exposure_type=self.exposure_type.get()
        )

    def update_prices(self, bid: float, ask: float):
        """Update current prices"""
        self.chart.update_prices(bid, ask)

    def update_history(self, bars):
        """Update price history"""
        self.chart.update_history(bars)

    def run(self, on_closing):
        """Start the GUI event loop"""
        self.root.protocol("WM_DELETE_WINDOW", on_closing)
        self.root.mainloop()

    def destroy(self):
        """Clean up and destroy the window"""
        self.root.quit()
        self.root.destroy()
