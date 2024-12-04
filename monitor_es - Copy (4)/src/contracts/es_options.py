"""ES Options Contract Management"""

from ib_insync import Future, FuturesOption
from datetime import datetime, timedelta
import logging
from .es_contract import ESContract
from .es_weeklies import get_weekly_trading_class, get_next_expiry

logger = logging.getLogger(__name__)


class ESOptionsManager:
    def __init__(self, ib):
        self.ib = ib
        self.contract_manager = ESContract(ib)

    def get_trading_class_for_date(self, expiry_date):
        """Get the correct trading class for a given expiration date"""
        try:
            # For now, use the known correct trading class
            trading_class = get_weekly_trading_class()
            logger.info(f"Using trading class {trading_class} for {expiry_date}")
            return trading_class

        except Exception as e:
            logger.error(f"Error determining trading class: {str(e)}")
            return None

    def get_current_es_price(self):
        """Get current ES futures price"""
        try:
            # Get active contract
            contract = self.contract_manager.get_active_contract()
            if not contract:
                return None

            ticker = self.ib.reqMktData(contract)
            self.ib.sleep(2)  # Wait for data

            price = None
            if ticker.last:
                price = ticker.last
            elif ticker.bid and ticker.ask:
                price = (ticker.bid + ticker.ask) / 2

            # Cancel market data subscription
            self.ib.cancelMktData(contract)

            return price

        except Exception as e:
            logger.error(f"Error getting ES price: {str(e)}")
            return None

    def get_available_strikes(self, trading_class, center_price):
        """Get available strikes for the trading class"""
        try:
            # Get active contract
            contract = self.contract_manager.get_active_contract()
            if not contract:
                return None

            # Request option chain parameters
            chains = self.ib.reqSecDefOptParams(
                underlyingSymbol="ES",
                futFopExchange="CME",
                underlyingSecType="FUT",
                underlyingConId=contract.conId,
            )

            if not chains:
                logger.error("No option chains received")
                return None

            # Find chain for our trading class
            chain = next((c for c in chains if c.tradingClass == trading_class), None)
            if not chain:
                logger.error(f"No chain found for trading class {trading_class}")
                return None

            # Get strikes within 150 points of center price
            strikes = sorted([s for s in chain.strikes if abs(s - center_price) <= 150])
            logger.info(f"Found {len(strikes)} strikes around {center_price}")
            return strikes

        except Exception as e:
            logger.error(f"Error getting strikes: {str(e)}")
            return None

    def create_option_contracts(self, strikes, expiry, trading_class):
        """Create option contracts for given strikes"""
        contracts = []
        for strike in strikes:
            try:
                call = FuturesOption(
                    symbol="ES",
                    lastTradeDateOrContractMonth=expiry,
                    strike=strike,
                    right="C",
                    exchange="CME",
                    currency="USD",
                    multiplier="50",
                    tradingClass=trading_class,
                )

                put = FuturesOption(
                    symbol="ES",
                    lastTradeDateOrContractMonth=expiry,
                    strike=strike,
                    right="P",
                    exchange="CME",
                    currency="USD",
                    multiplier="50",
                    tradingClass=trading_class,
                )

                qualified_call = self.ib.qualifyContracts(call)
                qualified_put = self.ib.qualifyContracts(put)

                if qualified_call and qualified_put:
                    contracts.append((strike, qualified_call[0], qualified_put[0]))
                    logger.info(f"Created contracts for strike {strike}")

            except Exception as e:
                logger.error(f"Error creating contracts for strike {strike}: {str(e)}")

        return contracts
