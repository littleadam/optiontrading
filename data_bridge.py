import os
import json
import pandas as pd
import datetime
import time
import logging
import sys
from pathlib import Path

# Add the trading app to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'nifty_trading_app'))

# Try to import from the trading app
try:
    from src.models.position import Position
    from src.models.order import Order
    from src.utils.logger import setup_logging
except ImportError:
    # If import fails, create dummy classes
    class Position:
        pass
    
    class Order:
        pass

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs', 'dashboard.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class TradingDataBridge:
    """
    Bridge between the trading application and the dashboard.
    Handles data synchronization and communication.
    """
    
    def __init__(self):
        """Initialize the data bridge."""
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        self.logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        
        # Create directories if they don't exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Paths for data files
        self.positions_path = os.path.join(self.data_dir, 'positions.csv')
        self.orders_path = os.path.join(self.data_dir, 'orders.csv')
        self.pnl_history_path = os.path.join(self.data_dir, 'pnl_history.csv')
        self.strategy_status_path = os.path.join(self.data_dir, 'strategy_status.json')
        
        # Initialize data files if they don't exist
        self._initialize_data_files()
        
        # Trading app log paths
        self.trading_app_log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                              'nifty_trading_app', 'logs')
        self.trading_app_log_path = os.path.join(self.trading_app_log_dir, 'trading_app.log')
        self.trading_app_error_log_path = os.path.join(self.trading_app_log_dir, 'error.log')
        
        # Create trading app log directory if it doesn't exist
        os.makedirs(self.trading_app_log_dir, exist_ok=True)
        
        # Initialize trading app log files if they don't exist
        self._initialize_log_files()
    
    def _initialize_data_files(self):
        """Initialize data files if they don't exist."""
        # Positions
        if not os.path.exists(self.positions_path):
            positions = pd.DataFrame({
                'symbol': ['NIFTY25MAY18000CE', 'NIFTY25MAY17000PE'],
                'quantity': [-75, -75],
                'average_price': [150.25, 145.75],
                'last_price': [155.50, 140.25],
                'pnl': [-393.75, 412.50],
                'timestamp': [datetime.datetime.now(), datetime.datetime.now()]
            })
            positions.to_csv(self.positions_path, index=False)
        
        # Orders
        if not os.path.exists(self.orders_path):
            orders = pd.DataFrame({
                'order_id': ['order1', 'order2', 'order3', 'order4'],
                'symbol': ['NIFTY25MAY18000CE', 'NIFTY25MAY17000PE', 'NIFTY25MAY18500CE', 'NIFTY25MAY16500PE'],
                'side': ['SELL', 'SELL', 'BUY', 'BUY'],
                'quantity': [75, 75, 75, 75],
                'price': [150.25, 145.75, 95.25, 45.50],
                'status': ['COMPLETE', 'COMPLETE', 'COMPLETE', 'COMPLETE'],
                'timestamp': [datetime.datetime.now() - datetime.timedelta(days=1),
                             datetime.datetime.now() - datetime.timedelta(days=1),
                             datetime.datetime.now() - datetime.timedelta(days=1),
                             datetime.datetime.now() - datetime.timedelta(days=1)]
            })
            orders.to_csv(self.orders_path, index=False)
        
        # P&L History
        if not os.path.exists(self.pnl_history_path):
            dates = pd.date_range(end=datetime.datetime.now(), periods=30)
            pnl_history = pd.DataFrame({
                'date': dates,
                'daily_pnl': [100 * (i - 15) for i in range(30)],
                'cumulative_pnl': [100 * sum(range(i+1)) for i in range(30)]
            })
            pnl_history.to_csv(self.pnl_history_path, index=False)
        
        # Strategy Status
        if not os.path.exists(self.strategy_status_path):
            status = {
                'running': False,
                'last_update': datetime.datetime.now().isoformat(),
                'start_time': None,
                'uptime': 0
            }
            with open(self.strategy_status_path, 'w') as f:
                json.dump(status, f)
    
    def _initialize_log_files(self):
        """Initialize log files if they don't exist."""
        # Trading app log
        if not os.path.exists(self.trading_app_log_path):
            with open(self.trading_app_log_path, 'w') as f:
                f.write("2025-05-18 08:00:00 - INFO - Starting Short Strangle strategy\n")
                f.write("2025-05-18 08:00:01 - INFO - Initialized strategy with 0 active positions\n")
                f.write("2025-05-18 08:00:02 - INFO - Calculated total investment: 200000\n")
                f.write("2025-05-18 08:00:03 - INFO - No active positions, placing initial short strangle\n")
                f.write("2025-05-18 08:00:04 - INFO - Placed order: SELL NIFTY25MAY18000CE at 18000\n")
                f.write("2025-05-18 08:00:05 - INFO - Placed order: SELL NIFTY25MAY17000PE at 17000\n")
        
        # Trading app error log
        if not os.path.exists(self.trading_app_error_log_path):
            with open(self.trading_app_error_log_path, 'w') as f:
                f.write("2025-05-18 08:00:10 - ERROR - Failed to fetch option chain master\n")
    
    def get_positions(self):
        """Get current positions."""
        try:
            return pd.read_csv(self.positions_path)
        except Exception as e:
            logger.error(f"Error reading positions: {str(e)}")
            return pd.DataFrame()
    
    def get_orders(self):
        """Get order history."""
        try:
            return pd.read_csv(self.orders_path)
        except Exception as e:
            logger.error(f"Error reading orders: {str(e)}")
            return pd.DataFrame()
    
    def get_pnl_history(self):
        """Get P&L history."""
        try:
            return pd.read_csv(self.pnl_history_path)
        except Exception as e:
            logger.error(f"Error reading P&L history: {str(e)}")
            return pd.DataFrame()
    
    def get_strategy_status(self):
        """Get strategy status."""
        try:
            with open(self.strategy_status_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading strategy status: {str(e)}")
            return {'running': False, 'last_update': datetime.datetime.now().isoformat(), 'start_time': None, 'uptime': 0}
    
    def set_strategy_status(self, running):
        """Set strategy status."""
        try:
            status = self.get_strategy_status()
            status['running'] = running
            status['last_update'] = datetime.datetime.now().isoformat()
            
            if running and not status['start_time']:
                status['start_time'] = datetime.datetime.now().isoformat()
            elif not running:
                status['start_time'] = None
                status['uptime'] = 0
            
            with open(self.strategy_status_path, 'w') as f:
                json.dump(status, f)
            
            return True
        except Exception as e:
            logger.error(f"Error setting strategy status: {str(e)}")
            return False
    
    def get_logs(self, max_lines=100):
        """Get trading app logs."""
        try:
            if os.path.exists(self.trading_app_log_path):
                with open(self.trading_app_log_path, 'r') as f:
                    logs = f.readlines()
                return logs[-max_lines:] if len(logs) > max_lines else logs
            return []
        except Exception as e:
            logger.error(f"Error reading logs: {str(e)}")
            return []
    
    def get_error_logs(self, max_lines=100):
        """Get trading app error logs."""
        try:
            if os.path.exists(self.trading_app_error_log_path):
                with open(self.trading_app_error_log_path, 'r') as f:
                    logs = f.readlines()
                return logs[-max_lines:] if len(logs) > max_lines else logs
            return []
        except Exception as e:
            logger.error(f"Error reading error logs: {str(e)}")
            return []
    
    def start_strategy(self):
        """Start the trading strategy."""
        try:
            # In a real implementation, this would start the trading application process
            # For now, we'll just update the status
            self.set_strategy_status(True)
            
            # Log the action
            logger.info("Strategy started")
            
            # Append to trading app log
            with open(self.trading_app_log_path, 'a') as f:
                f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Strategy started\n")
            
            return True
        except Exception as e:
            logger.error(f"Error starting strategy: {str(e)}")
            return False
    
    def stop_strategy(self):
        """Stop the trading strategy."""
        try:
            # In a real implementation, this would stop the trading application process
            # For now, we'll just update the status
            self.set_strategy_status(False)
            
            # Log the action
            logger.info("Strategy stopped")
            
            # Append to trading app log
            with open(self.trading_app_log_path, 'a') as f:
                f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Strategy stopped\n")
            
            return True
        except Exception as e:
            logger.error(f"Error stopping strategy: {str(e)}")
            return False
    
    def close_all_positions(self):
        """Close all positions."""
        try:
            # In a real implementation, this would close all positions
            # For now, we'll just log the action
            logger.info("Closing all positions")
            
            # Append to trading app log
            with open(self.trading_app_log_path, 'a') as f:
                f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Closing all positions\n")
            
            # Update positions to zero
            positions = self.get_positions()
            positions['quantity'] = 0
            positions['pnl'] = 0
            positions['timestamp'] = datetime.datetime.now()
            positions.to_csv(self.positions_path, index=False)
            
            return True
        except Exception as e:
            logger.error(f"Error closing positions: {str(e)}")
            return False
    
    def update_data(self):
        """Update data from the trading application."""
        try:
            # In a real implementation, this would fetch data from the trading application
            # For now, we'll just update the timestamps
            
            # Update positions
            positions = self.get_positions()
            if not positions.empty:
                positions['timestamp'] = datetime.datetime.now()
                positions.to_csv(self.positions_path, index=False)
            
            # Update P&L history
            pnl_history = self.get_pnl_history()
            if not pnl_history.empty:
                # Add today's P&L if not already present
                today = datetime.datetime.now().date()
                if not any(pd.to_datetime(pnl_history['date']).dt.date == today):
                    last_pnl = pnl_history['cumulative_pnl'].iloc[-1]
                    daily_pnl = round(last_pnl * 0.01 * (0.5 - random.random()), 2)  # Random daily P&L
                    new_row = pd.DataFrame({
                        'date': [today],
                        'daily_pnl': [daily_pnl],
                        'cumulative_pnl': [last_pnl + daily_pnl]
                    })
                    pnl_history = pd.concat([pnl_history, new_row], ignore_index=True)
                    pnl_history.to_csv(self.pnl_history_path, index=False)
            
            # Update strategy status
            status = self.get_strategy_status()
            if status['running'] and status['start_time']:
                start_time = datetime.datetime.fromisoformat(status['start_time'])
                uptime = (datetime.datetime.now() - start_time).total_seconds()
                status['uptime'] = uptime
                with open(self.strategy_status_path, 'w') as f:
                    json.dump(status, f)
            
            return True
        except Exception as e:
            logger.error(f"Error updating data: {str(e)}")
            return False

# For testing
if __name__ == "__main__":
    import random
    
    bridge = TradingDataBridge()
    
    # Test data update
    bridge.update_data()
    
    # Test strategy control
    bridge.start_strategy()
    time.sleep(1)
    bridge.stop_strategy()
    
    # Test position closing
    bridge.close_all_positions()
    
    print("Data bridge test complete")
