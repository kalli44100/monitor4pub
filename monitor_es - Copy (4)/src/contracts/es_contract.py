"""ES Contract Management"""
from ib_insync import IB, Future
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class ESContract:
    def __init__(self, ib: IB):
        self.ib = ib
        
    def get_active_contract(self) -> Optional[Future]:
        """Get the currently active ES futures contract"""
        try:
            # Request contract details to find active contracts
            es_future = Future(symbol='ES', exchange='CME', currency='USD')
            details = self.ib.reqContractDetails(es_future)
            
            if not details:
                logger.error("No ES futures contracts found")
                return None
                
            # Find the nearest quarterly contract
            now = datetime.now()
            active_contract = None
            min_days = float('inf')
            
            for detail in details:
                contract = detail.contract
                expiry = datetime.strptime(contract.lastTradeDateOrContractMonth, '%Y%m%d')
                days_to_expiry = (expiry - now).days
                
                # Only consider contracts that haven't expired
                if days_to_expiry > 0 and days_to_expiry < min_days:
                    min_days = days_to_expiry
                    active_contract = contract
                    
            return active_contract
            
        except Exception as e:
            logger.error(f"Error getting active contract: {str(e)}")
            return None
            
    def get_next_expiry(self) -> Optional[Tuple[datetime, str]]:
        """Get next options expiration and trading class"""
        try:
            now = datetime.now()
            today = now.date()
            
            # Find next Friday
            days_to_friday = (4 - today.weekday()) % 7
            next_friday = today + timedelta(days=days_to_friday)
            
            # If it's Friday after cutoff (3:15 PM CT), use next week
            if (today.weekday() == 4 and 
                ((now.hour > 15) or (now.hour == 15 and now.minute >= 15))):
                next_friday += timedelta(days=7)
                
            # Get trading class based on week
            week_code = chr(65)  # 'A' for current week
            if days_to_friday > 7:
                week_code = chr(66)  # 'B' for next week
                
            trading_class = f"E1{week_code}"
            
            logger.info(f"Next expiry: {next_friday}, Trading class: {trading_class}")
            return (next_friday, trading_class)
            
        except Exception as e:
            logger.error(f"Error getting next expiry: {str(e)}")
            return None