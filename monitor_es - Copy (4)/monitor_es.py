"""ES Options Monitor Main Application"""

import logging
import sys
from datetime import datetime
from ib_insync import IB
from src.gui import ESOptionsWindow
from src.contracts import ESOptionsManager
from src.market_data import OptionsDataProcessor
from src.market_data.historical_data import request_historical_data
from src.contracts.es_contract import ESContract

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


class MarketMonitor:
    def __init__(self):
        logger.info("\n=== ES Options Monitor Starting ===\n")

        self.ib = IB()
        self.connected = False
        self.is_refreshing = False

        # Initialize components
        self.window = ESOptionsWindow(
            on_refresh=self.refresh_options,
            on_cancel=self.cancel_refresh,
            on_connect=self.toggle_connection,
        )
        self.contract_manager = ESContract(self.ib)
        self.options_manager = ESOptionsManager(self.ib)
        self.data_processor = OptionsDataProcessor(self.ib)

    def load_historical_data(self):
        """Load historical price data"""
        try:
            # Get active contract
            contract = self.contract_manager.get_active_contract()
            if not contract:
                logger.error("Could not get ES contract")
                return

            # Request historical data
            bars = request_historical_data(self.ib, contract)
            if bars:
                logger.info(f"Loaded {len(bars)} historical bars")
                self.window.update_history(bars)

                # Set up price updates
                ticker = self.ib.reqMktData(contract)
                if hasattr(ticker, "bid") and hasattr(ticker, "ask"):
                    self.window.update_prices(ticker.bid, ticker.ask)

        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")

    def cancel_refresh(self):
        """Cancel the refresh operation"""
        self.is_refreshing = False
        self.window.set_refresh_state(False)
        self.data_processor.cleanup()

    def refresh_options(self):
        """Refresh options data"""
        logger.info("Refreshing options data...")
        try:
            if not self.connected:
                logger.warning("Not connected to IB")
                return

            self.is_refreshing = True
            self.window.set_refresh_state(True)
            self.data_processor.cleanup()

            # Get current price and trading class
            current_price = self.options_manager.get_current_es_price()
            if not current_price:
                logger.error("Could not get current ES price")
                return

            today = datetime.now().date()
            trading_class = "E1B"  # Use known correct trading class
            if not trading_class:
                logger.error("Could not determine trading class")
                return

            # Get available strikes
            strikes = self.options_manager.get_available_strikes(
                trading_class, current_price
            )
            if not strikes:
                logger.error("Could not get available strikes")
                return

            # Create contracts
            expiry = today.strftime("%Y%m%d")
            contracts = self.options_manager.create_option_contracts(
                strikes, expiry, trading_class
            )

            if not contracts:
                logger.error("No valid contracts created")
                return

            # Request and process market data
            tickers = self.data_processor.request_market_data(contracts, current_price)
            delta_data, max_exposure = self.data_processor.process_market_data(
                tickers, self.window.exposure_type.get()
            )

            # Update chart
            if delta_data:
                self.window.update_chart(delta_data, max_exposure, current_price)
                logger.info("Options refresh completed")

        except Exception as e:
            logger.error(f"Error refreshing options: {str(e)}")
        finally:
            self.is_refreshing = False
            self.window.set_refresh_state(False)

    def toggle_connection(self):
        """Toggle IB connection"""
        if not self.connected:
            self.connect()
        else:
            self.disconnect()

    def connect(self):
        """Connect to IB Gateway"""
        try:
            logger.info("Attempting to connect to IB Gateway...")
            self.window.conn_status.config(text="Connecting...", fg="orange")

            self.ib.connect("127.0.0.1", 4001, clientId=1)
            self.connected = True
            self.window.update_connection_status(True)

            # Load historical data
            self.load_historical_data()

            self.update_loop()
            logger.info("Successfully connected to IB Gateway")

        except Exception as e:
            logger.error(f"Connection error: {str(e)}")
            self.window.update_connection_status(False, str(e))
            self.connected = False

    def disconnect(self):
        """Disconnect from IB Gateway"""
        try:
            logger.info("Disconnecting from IB Gateway...")
            self.data_processor.cleanup()

            if self.ib.isConnected():
                self.ib.disconnect()

            self.connected = False
            self.window.update_connection_status(False)
            logger.info("Disconnected from IB Gateway")

        except Exception as e:
            logger.error(f"Error during disconnect: {str(e)}")

    def update_loop(self):
        """Main update loop"""
        try:
            if self.connected and self.ib.isConnected():
                self.ib.sleep(0.1)
                self.window.root.after(100, self.update_loop)
            else:
                self.disconnect()
        except Exception as e:
            logger.error(f"Error in update loop: {str(e)}")
            self.disconnect()

    def run(self):
        """Run the application"""
        try:
            self.window.run(self.on_closing)
        except Exception as e:
            logger.error(f"Error running application: {str(e)}")

    def on_closing(self):
        """Handle application shutdown"""
        logger.info("Shutting down application...")
        try:
            self.disconnect()
            self.window.destroy()
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            sys.exit(0)


if __name__ == "__main__":
    try:
        app = MarketMonitor()
        app.run()
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}")
        sys.exit(1)
