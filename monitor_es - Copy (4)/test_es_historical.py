"""Test ES Futures Historical Data Import"""
from ib_insync import IB, Future
import logging
import sys
from datetime import datetime, timedelta
from src.market_data.historical_data import request_historical_data, format_bar_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def test_es_historical():
    ib = IB()
    try:
        logger.info("Connecting to IB Gateway...")
        ib.connect('127.0.0.1', 4001, clientId=1)
        
        # Create ES Future contract
        es_future = Future(
            symbol='ES',
            lastTradeDateOrContractMonth='20241220',  # December 2024 contract
            exchange='CME',
            currency='USD',
            localSymbol='ESZ4'  # ES December 2024
        )
        
        logger.info("\nTesting ES Future Historical Data:")
        logger.info(f"Contract: {es_future}")
        
        # Test different time periods
        test_periods = [
            ("1 D", "1 min", "Last day - 1 minute bars"),
            ("1 W", "1 hour", "Last week - 1 hour bars"),
            ("1 M", "1 day", "Last month - daily bars")
        ]
        
        for duration, bar_size, description in test_periods:
            logger.info(f"\nRetrieving {description}...")
            
            bars = request_historical_data(
                ib,
                es_future,
                duration=duration,
                bar_size=bar_size
            )
            
            if bars:
                logger.info(f"Retrieved {len(bars)} bars")
                
                # Show first and last few bars
                logger.info("\nFirst 3 bars:")
                for bar in bars[:3]:
                    logger.info(format_bar_data(bar))
                    
                logger.info("\nLast 3 bars:")
                for bar in bars[-3:]:
                    logger.info(format_bar_data(bar))
                    
                # Calculate some basic statistics
                closes = [bar.close for bar in bars]
                if closes:
                    avg_price = sum(closes) / len(closes)
                    max_price = max(closes)
                    min_price = min(closes)
                    
                    logger.info("\nPrice Statistics:")
                    logger.info(f"Average Price: {avg_price:.2f}")
                    logger.info(f"Maximum Price: {max_price:.2f}")
                    logger.info(f"Minimum Price: {min_price:.2f}")
                    logger.info(f"Price Range: {(max_price - min_price):.2f}")
            else:
                logger.warning(f"No data received for {description}")
                
    except Exception as e:
        logger.error(f"Test error: {str(e)}")
    finally:
        if ib.isConnected():
            ib.disconnect()
        logger.info("\nTest completed")

if __name__ == "__main__":
    test_es_historical()