import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import time
import datetime
import random
import sys
from pathlib import Path

# Set up paths
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(dashboard_dir, 'data')
logs_dir = os.path.join(dashboard_dir, 'logs')

# Create directories if they don't exist
os.makedirs(data_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

# Data bridge class for handling data
class TradingDataBridge:
    """
    Bridge between the trading application and the dashboard.
    Handles data synchronization and communication.
    """
    
    def __init__(self):
        """Initialize the data bridge."""
        self.data_dir = data_dir
        self.logs_dir = logs_dir
        
        # Paths for data files
        self.positions_path = os.path.join(self.data_dir, 'positions.csv')
        self.orders_path = os.path.join(self.data_dir, 'orders.csv')
        self.pnl_history_path = os.path.join(self.data_dir, 'pnl_history.csv')
        self.strategy_status_path = os.path.join(self.data_dir, 'strategy_status.json')
        
        # Initialize data files if they don't exist
        self._initialize_data_files()
        
        # Trading app log paths
        self.trading_app_log_path = os.path.join(self.logs_dir, 'trading_app.log')
        self.trading_app_error_log_path = os.path.join(self.logs_dir, 'error.log')
        
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
            st.error(f"Error reading positions: {str(e)}")
            return pd.DataFrame()
    
    def get_orders(self):
        """Get order history."""
        try:
            return pd.read_csv(self.orders_path)
        except Exception as e:
            st.error(f"Error reading orders: {str(e)}")
            return pd.DataFrame()
    
    def get_pnl_history(self):
        """Get P&L history."""
        try:
            return pd.read_csv(self.pnl_history_path)
        except Exception as e:
            st.error(f"Error reading P&L history: {str(e)}")
            return pd.DataFrame()
    
    def get_strategy_status(self):
        """Get strategy status."""
        try:
            with open(self.strategy_status_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error reading strategy status: {str(e)}")
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
            st.error(f"Error setting strategy status: {str(e)}")
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
            st.error(f"Error reading logs: {str(e)}")
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
            st.error(f"Error reading error logs: {str(e)}")
            return []
    
    def start_strategy(self):
        """Start the trading strategy."""
        try:
            # In a real implementation, this would start the trading application process
            # For now, we'll just update the status
            self.set_strategy_status(True)
            
            # Append to trading app log
            with open(self.trading_app_log_path, 'a') as f:
                f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Strategy started\n")
            
            return True
        except Exception as e:
            st.error(f"Error starting strategy: {str(e)}")
            return False
    
    def stop_strategy(self):
        """Stop the trading strategy."""
        try:
            # In a real implementation, this would stop the trading application process
            # For now, we'll just update the status
            self.set_strategy_status(False)
            
            # Append to trading app log
            with open(self.trading_app_log_path, 'a') as f:
                f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Strategy stopped\n")
            
            return True
        except Exception as e:
            st.error(f"Error stopping strategy: {str(e)}")
            return False
    
    def close_all_positions(self):
        """Close all positions."""
        try:
            # In a real implementation, this would close all positions
            # For now, we'll just log the action
            
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
            st.error(f"Error closing positions: {str(e)}")
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
            st.error(f"Error updating data: {str(e)}")
            return False

# Initialize data bridge
data_bridge = TradingDataBridge()

# Helper functions
def load_config():
    """Load configuration or return default config"""
    # Default config
    return {
        "API_CONFIG": {
            "api_key": "",
            "api_url": "https://api.mstock.trade",
            "ws_url": "https://ws.mstock.trade",
            "version": "1"
        },
        "INVESTMENT_CONFIG": {
            "base_investment": 200000,
            "lot_size": 75,
            "lots_per_investment": 1,
            "investment_per_lot": 150000,
        },
        "STRATEGY_CONFIG": {
            "target_monthly_return": 0.04,
            "leg_premium_target": 0.02,
            "strangle_distance": 1000,
            "sell_expiry_weeks": 4,
            "hedge_expiry_weeks": 1,
            "stop_loss_trigger": 0.25,
            "stop_loss_percentage": 0.90,
            "martingale_trigger": 2.0,
            "martingale_quantity_multiplier": 2.0,
            "martingale_premium_divisor": 2.0,
        },
        "TRADING_HOURS": {
            "start_time": "09:15:00",
            "end_time": "15:30:00",
            "check_interval": 300,
        },
        "HOLIDAYS": [],
        "LOGGING_CONFIG": {
            "log_level": "INFO",
            "log_file": "trading_app.log",
            "error_log_file": "error.log",
        }
    }

def save_config(config):
    """Save configuration to a JSON file"""
    config_path = os.path.join(data_dir, 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    return True

# Set page configuration
st.set_page_config(
    page_title="Nifty 50 Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #0D47A1;
        margin-top: 1rem;
        margin-bottom: 0.5rem;
    }
    .status-active {
        color: #4CAF50;
        font-weight: bold;
    }
    .status-inactive {
        color: #F44336;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    .log-container {
        height: 300px;
        overflow-y: auto;
        background-color: #f5f5f5;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
    }
    .error-log {
        color: #F44336;
    }
    .warning-log {
        color: #FF9800;
    }
    .info-log {
        color: #2196F3;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'strategy_running' not in st.session_state:
    status = data_bridge.get_strategy_status()
    st.session_state.strategy_running = status['running']

# Update data
data_bridge.update_data()

# Main dashboard layout
st.markdown("<h1 class='main-header'>Nifty 50 Trading Dashboard</h1>", unsafe_allow_html=True)

# Status and controls
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.subheader("Strategy Status")
    if st.session_state.strategy_running:
        st.markdown("<p class='status-active'>● ACTIVE</p>", unsafe_allow_html=True)
        status = data_bridge.get_strategy_status()
        if status['start_time']:
            start_time = datetime.datetime.fromisoformat(status['start_time'])
            uptime = datetime.datetime.now() - start_time
            st.write(f"Running since: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            st.write(f"Uptime: {uptime}")
    else:
        st.markdown("<p cla
(Content truncated due to size limit. Use line ranges to read in chunks)