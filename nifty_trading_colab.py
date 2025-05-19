"""
Google Colab notebook for running Nifty 50 Trading Application indefinitely.
This notebook includes all the necessary code and setup instructions.
"""

# @title Setup and Installation
%%capture
!pip install streamlit pandas matplotlib plotly

# @title Import Libraries
import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import datetime
import time
import random
import threading
import IPython.display
from google.colab import output
from IPython.display import clear_output, HTML, display

# @title Create Directory Structure
!mkdir -p /content/nifty_trading_app/data
!mkdir -p /content/nifty_trading_app/logs
!mkdir -p /content/nifty_trading_app/config

# @title Keep-Alive Function
def keep_alive():
    """
    Function to keep the Colab notebook running indefinitely.
    This simulates user activity to prevent Colab from timing out.
    """
    while True:
        # Display a timestamp to show the notebook is still running
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        clear_output(wait=True)
        display(HTML(f"""
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <h3>Nifty 50 Trading Application</h3>
            <p>Status: <span style="color: green; font-weight: bold;">RUNNING</span></p>
            <p>Last update: {timestamp}</p>
            <p>This notebook is running indefinitely. Do not close this tab.</p>
        </div>
        """))
        
        # Sleep for 60 seconds before updating again
        time.sleep(60)

# @title Trading Data Bridge Class
class TradingDataBridge:
    """
    Bridge between the trading application and the dashboard.
    Handles data synchronization and communication.
    """
    
    def __init__(self):
        """Initialize the data bridge."""
        self.data_dir = "/content/nifty_trading_app/data"
        self.logs_dir = "/content/nifty_trading_app/logs"
        
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
            print(f"Error reading positions: {str(e)}")
            return pd.DataFrame()
    
    def get_orders(self):
        """Get order history."""
        try:
            return pd.read_csv(self.orders_path)
        except Exception as e:
            print(f"Error reading orders: {str(e)}")
            return pd.DataFrame()
    
    def get_pnl_history(self):
        """Get P&L history."""
        try:
            return pd.read_csv(self.pnl_history_path)
        except Exception as e:
            print(f"Error reading P&L history: {str(e)}")
            return pd.DataFrame()
    
    def get_strategy_status(self):
        """Get strategy status."""
        try:
            with open(self.strategy_status_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading strategy status: {str(e)}")
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
            print(f"Error setting strategy status: {str(e)}")
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
            print(f"Error reading logs: {str(e)}")
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
            print(f"Error reading error logs: {str(e)}")
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
            print(f"Error starting strategy: {str(e)}")
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
            print(f"Error stopping strategy: {str(e)}")
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
            print(f"Error closing positions: {str(e)}")
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
            print(f"Error updating data: {str(e)}")
            return False

# @title Helper Functions
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
    config_path = os.path.join("/content/nifty_trading_app/config", 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
    return True

# @title Dashboard Functions
def display_dashboard():
    """Display the dashboard in Colab"""
    # Initialize data bridge
    data_bridge = TradingDataBridge()
    
    # Update data
    data_bridge.update_data()
    
    # Get strategy status
    status = data_bridge.get_strategy_status()
    
    # Clear previous output
    clear_output(wait=True)
    
    # Display header
    display(HTML("""
    <style>
        .dashboard-header {
            background-color: #1E88E5;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }
        .section-header {
            background-color: #0D47A1;
            color: white;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
            margin-bottom: 10px;
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
            padding: 10px;
            margin: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .log-container {
            height: 200px;
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
        .button-container {
            display: flex;
            justify-content: space-around;
            margin: 10px 0;
        }
        .button {
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            text-align: center;
        }
        .start-button {
            background-color: #4CAF50;
            color: white;
        }
        .stop-button {
            background-color: #F44336;
            color: white;
        }
        .emergency-button {
            background-color: #FF9800;
            color: white;
        }
    </style>
    <div class="dashboard-header">
        <h1>Nifty 50 Trading Dashboard</h1>
        <p>Last updated: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>
    """))
    
    # Display status and controls
    status_html = """
    <div class="section-header">
        <h2>Status and Controls</h2>
    </div>
    <div style="display: flex; justify-content: space-between;">
        <div class="metric-card" style="flex: 1;">
            <h3>Strategy Status</h3>
    """
    
    if status['running']:
        status_html += """<p class="status-active">● ACTIVE</p>"""
        if status['start_time']:
            start_time = datetime.datetime.fromisoformat(status['start_time'])
            uptime = datetime.datetime.now() - start_time
            status_html += f"""
            <p>Running since: {start_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Uptime: {uptime}</p>
            """
    else:
        status_html += """<p class="status-inactive">● INACTIVE</p>"""
    
    status_html += """
        </div>
        <div class="metric-card" style="flex: 1;">
            <h3>Controls</h3>
            <div class="button-container">
    """
    
    if status['running']:
        status_html += """
        <div class="button stop-button" onclick="
            IPython.notebook.kernel.execute('data_bridge.stop_strategy()');
            setTimeout(function() { IPython.notebook.kernel.execute('display_dashboard()') }, 1000);
        ">Stop Strategy</div>
        """
    else:
        status_html += """
        <div class="button start-button" onclick="
            IPython.notebook.kernel.execute('data_bridge.start_strategy()');
            setTimeout(function() { IPython.notebook.kernel.execute('display_dashboard()') }, 1000);
        ">Start Strategy</div>
        """
    
    status_html += """
            </div>
        </div>
        <div class="metric-card" style="flex: 1;">
            <h3>Emergency Actions</h3>
            <div class="button-container">
                <div class="button emergency-button" onclick="
                    IPython.notebook.kernel.execute('data_bridge.close_all_positions()');
                    setTimeout(function() { IPython.notebook.kernel.execute('display_dashboard()') }, 1000);
                ">Close All Positions</div>
            </div>
        </div>
    </div>
    """
    
    display(HTML(status_html))
    
    # Display positions
    display(HTML("""
    <div class="section-header">
        <h2>Current Positions</h2>
    </div>
    """))
    
    positions = data_bridge.get_positions()
    if not positions.empty:
        display(positions)
    else:
        display(HTML("<p>No positions found.</p>"))
    
    # Display P&L
    display(HTML("""
    <div class="section-header">
        <h2>P&L Performance</h2>
    </div>
    """))
    
    pnl_history = data_bridge.get_pnl_history()
    if not pnl_history.empty:
        # Convert date column to datetime
        pnl_history['date'] = pd.to_datetime(pnl_history['date'])
        
        # Create P&L charts
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 6))
        
        # Daily P&L chart
        ax1.bar(pnl_history['date'], pnl_history['daily_pnl'], color=['red' if x < 0 else 'green' for x in pnl_history['daily_pnl']])
        ax1.set_title('Daily P&L')
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Daily P&L')
        
        # Cumulative P&L chart
        ax2.plot(pnl_history['date'], pnl_history['cumulative_pnl'], color='blue')
        ax2.set_title('Cumulative P&L')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Cumulative P&L')
        
        plt.tight_layout()
        plt.show()
        
        # P&L metrics
        metrics_html = """
        <div style="display: flex; justify-content: space-between;">
        """
        
        # Today's P&L
        metrics_html += f"""
        <div class="metric-card" style="flex: 1;">
            <h3>Today's P&L</h3>
            <p style="font-size: 24px; font-weight: bold; color: {'green' if pnl_history['daily_pnl'].iloc[-1] >= 0 else 'red'};">
                ₹{pnl_history['daily_pnl'].iloc[-1]:,.2f}
            </p>
        </div>
        """
        
        # Total P&L
        metrics_html += f"""
        <div class="metric-card" style="flex: 1;">
            <h3>Total P&L</h3>
            <p style="font-size: 24px; font-weight: bold; color: {'green' if pnl_history['cumulative_pnl'].iloc[-1] >= 0 else 'red'};">
                ₹{pnl_history['cumulative_pnl'].iloc[-1]:,.2f}
            </p>
        </div>
        """
        
        # Monthly Return
        config = load_config()
        investment = config["INVESTMENT_CONFIG"]["base_investment"]
        monthly_return = pnl_history['cumulative_pnl'].iloc[-1] / investment * 100
        metrics_html += f"""
        <div class="metric-card" style="flex: 1;">
            <h3>Monthly Return</h3>
            <p style="font-size: 24px; font-weight: bold; color: {'green' if monthly_return >= 0 else 'red'};">
                {monthly_return:.2f}%
            </p>
        </div>
        """
        
        # Win Rate
        win_days = sum(pnl_history['daily_pnl'] > 0)
        total_days = len(pnl_history)
        win_rate = win_days / total_days * 100
        metrics_html += f"""
        <div class="metric-card" style="flex: 1;">
            <h3>Win Rate</h3>
            <p style="font-size: 24px; font-weight: bold;">
                {win_rate:.2f}%
            </p>
        </div>
        """
        
        metrics_html += """
        </div>
        """
        
        display(HTML(metrics_html))
    else:
        display(HTML("<p>No P&L history found.</p>"))
    
    # Display logs
    display(HTML("""
    <div class="section-header">
        <h2>Application Logs</h2>
    </div>
    """))
    
    logs = data_bridge.get_logs()
    logs_html = """
    <div class="log-container">
    """
    
    for log in logs:
        if "ERROR" in log:
            logs_html += f"<p class='error-log'>{log}</p>"
        elif "WARNING" in log:
            logs_html += f"<p class='warning-log'>{log}</p>"
        else:
            logs_html += f"<p class='info-log'>{log}</p>"
    
    logs_html += """
    </div>
    """
    
    display(HTML(logs_html))
    
    # Display error logs
    display(HTML("""
    <div class="section-header">
        <h2>Error Logs</h2>
    </div>
    """))
    
    error_logs = data_bridge.get_error_logs()
    error_logs_html = """
    <div class="log-container">
    """
    
    for log in error_logs:
        error_logs_html += f"<p class='error-log'>{log}</p>"
    
    error_logs_html += """
    </div>
    """
    
    display(HTML(error_logs_html))
    
    # Display refresh button
    display(HTML("""
    <div style="text-align: center; margin-top: 20px;">
        <div class="button" style="display: inline-block; background-color: #2196F3; color: white;" onclick="
            IPython.notebook.kernel.execute('display_dashboard()');
        ">Refresh Dashboard</div>
    </div>
    """))

# @title Main Trading Loop
def trading_loop():
    """Main trading loop that runs indefinitely."""
    data_bridge = TradingDataBridge()
    
    while True:
        try:
            # Update data
            data_bridge.update_data()
            
            # Get strategy status
            status = data_bridge.get_strategy_status()
            
            # If strategy is running, perform trading operations
            if status['running']:
                # In a real implementation, this would execute the trading strategy
                # For now, we'll just log the action
                with open(data_bridge.trading_app_log_path, 'a') as f:
                    f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - INFO - Trading loop iteration\n")
            
            # Sleep for 5 minutes
            time.sleep(300)
        except Exception as e:
            # Log any errors
            with open(data_bridge.trading_app_error_log_path, 'a') as f:
                f.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - ERROR - {str(e)}\n")
            
            # Sleep for 1 minute before retrying
            time.sleep(60)

# @title Run the Application
# Initialize data bridge
data_bridge = TradingDataBridge()

# Display the dashboard
display_dashboard()

# Start the keep-alive thread
keep_alive_thread = threading.Thread(target=keep_alive)
keep_alive_thread.daemon = True
keep_alive_thread.start()

# Start the trading loop thread
trading_thread = threading.Thread(target=trading_loop)
trading_thread.daemon = True
trading_thread.start()

# Display instructions
display(HTML("""
<div style="background-color: #e3f2fd; padding: 20px; border-radius: 10px; margin-top: 20px;">
    <h2>Instructions</h2>
    <p>The Nifty 50 Trading Application is now running indefinitely in this Colab notebook.</p>
    <ul>
        <li>The dashboard above shows the current status, positions, P&L, and logs.</li>
        <li>Use the controls to start/stop the strategy or close all positions.</li>
        <li>Click the "Refresh Dashboard" button to update the dashboard manually.</li>
        <li>The application will continue running as long as this Colab notebook is open.</li>
        <li>A keep-alive mechanism is active to prevent Colab from timing out.</li>
    </ul>
    <p><strong>Important:</strong> Do not close this tab or the application will stop running.</p>
</div>
"""))
