import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import json
import os
import time
import datetime
import sys
from pathlib import Path

# Set up paths
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(os.path.dirname(dashboard_dir), 'nifty_trading_app')

# Add the trading app to the path if it exists
if os.path.exists(app_dir):
    sys.path.append(app_dir)

# Import the data bridge
try:
    from data_bridge import TradingDataBridge
    data_bridge = TradingDataBridge()
except ImportError:
    # Create a dummy data bridge if the real one is not available
    class DummyDataBridge:
        def get_positions(self):
            return pd.DataFrame({
                'symbol': ['NIFTY25MAY18000CE', 'NIFTY25MAY17000PE'],
                'quantity': [-75, -75],
                'average_price': [150.25, 145.75],
                'last_price': [155.50, 140.25],
                'pnl': [-393.75, 412.50],
                'timestamp': [datetime.datetime.now(), datetime.datetime.now()]
            })
        
        def get_pnl_history(self):
            dates = pd.date_range(end=datetime.datetime.now(), periods=30)
            return pd.DataFrame({
                'date': dates,
                'daily_pnl': [100 * (i - 15) for i in range(30)],
                'cumulative_pnl': [100 * sum(range(i+1)) for i in range(30)]
            })
        
        def get_logs(self, max_lines=100):
            return [
                "2025-05-18 08:00:00 - INFO - Starting Short Strangle strategy\n",
                "2025-05-18 08:00:01 - INFO - Initialized strategy with 0 active positions\n",
                "2025-05-18 08:00:02 - INFO - Calculated total investment: 200000\n"
            ]
        
        def get_error_logs(self, max_lines=100):
            return ["2025-05-18 08:00:10 - ERROR - Failed to fetch option chain master\n"]
        
        def get_strategy_status(self):
            return {'running': False, 'last_update': datetime.datetime.now().isoformat(), 'start_time': None, 'uptime': 0}
        
        def start_strategy(self):
            return True
        
        def stop_strategy(self):
            return True
        
        def close_all_positions(self):
            return True
        
        def update_data(self):
            return True
    
    data_bridge = DummyDataBridge()

# Helper functions
def load_config():
    """Load configuration from the config file or return default config"""
    config_path = os.path.join(app_dir, 'config', 'config.py') if os.path.exists(app_dir) else None
    
    # Default config
    default_config = {
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
    
    # If config file doesn't exist, return default config
    if not config_path or not os.path.exists(config_path):
        return default_config
    
    # Parse the config file
    config = {}
    with open(config_path, 'r') as f:
        content = f.read()
        
        # Extract API_CONFIG
        if "API_CONFIG" in content:
            api_config_str = content.split("API_CONFIG = ")[1].split("}")[0] + "}"
            api_config_str = api_config_str.replace("'", "\"")
            try:
                config["API_CONFIG"] = json.loads(api_config_str)
            except:
                config["API_CONFIG"] = default_config["API_CONFIG"]
            
        # Extract INVESTMENT_CONFIG
        if "INVESTMENT_CONFIG" in content:
            investment_config_str = content.split("INVESTMENT_CONFIG = ")[1].split("}")[0] + "}"
            investment_config_str = investment_config_str.replace("'", "\"")
            try:
                config["INVESTMENT_CONFIG"] = json.loads(investment_config_str)
            except:
                config["INVESTMENT_CONFIG"] = default_config["INVESTMENT_CONFIG"]
            
        # Extract STRATEGY_CONFIG
        if "STRATEGY_CONFIG" in content:
            strategy_config_str = content.split("STRATEGY_CONFIG = ")[1].split("}")[0] + "}"
            strategy_config_str = strategy_config_str.replace("'", "\"")
            try:
                config["STRATEGY_CONFIG"] = json.loads(strategy_config_str)
            except:
                config["STRATEGY_CONFIG"] = default_config["STRATEGY_CONFIG"]
            
        # Extract TRADING_HOURS
        if "TRADING_HOURS" in content:
            trading_hours_str = content.split("TRADING_HOURS = ")[1].split("}")[0] + "}"
            trading_hours_str = trading_hours_str.replace("'", "\"")
            try:
                config["TRADING_HOURS"] = json.loads(trading_hours_str)
            except:
                config["TRADING_HOURS"] = default_config["TRADING_HOURS"]
            
        # Extract HOLIDAYS
        if "HOLIDAYS" in content:
            holidays_str = content.split("HOLIDAYS = ")[1].split("]")[0] + "]"
            holidays_str = holidays_str.replace("'", "\"")
            try:
                config["HOLIDAYS"] = json.loads(holidays_str)
            except:
                config["HOLIDAYS"] = default_config["HOLIDAYS"]
            
        # Extract LOGGING_CONFIG
        if "LOGGING_CONFIG" in content:
            logging_config_str = content.split("LOGGING_CONFIG = ")[1].split("}")[0] + "}"
            logging_config_str = logging_config_str.replace("'", "\"")
            try:
                config["LOGGING_CONFIG"] = json.loads(logging_config_str)
            except:
                config["LOGGING_CONFIG"] = default_config["LOGGING_CONFIG"]
    
    # Fill in any missing sections with defaults
    for key in default_config:
        if key not in config:
            config[key] = default_config[key]
    
    return config

def save_config(config):
    """Save configuration to the config file"""
    config_dir = os.path.join(app_dir, 'config')
    config_path = os.path.join(config_dir, 'config.py')
    
    # Create config directory if it doesn't exist
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    
    content = """\"\"\"
Configuration file for the Nifty 50 trading application.
All parameters are configurable to allow easy adjustment of the trading strategy.
\"\"\"

# API Configuration
API_CONFIG = {
    "api_key": "%s",
    "api_url": "%s",
    "ws_url": "%s",
    "version": "%s"
}

# Investment Configuration
INVESTMENT_CONFIG = {
    "base_investment": %d,
    "lot_size": %d,
    "lots_per_investment": %d,
    "investment_per_lot": %d,
}

# Strategy Configuration
STRATEGY_CONFIG = {
    "target_monthly_return": %.2f,
    "leg_premium_target": %.2f,
    "strangle_distance": %d,
    "sell_expiry_weeks": %d,
    "hedge_expiry_weeks": %d,
    "stop_loss_trigger": %.2f,
    "stop_loss_percentage": %.2f,
    "martingale_trigger": %.2f,
    "martingale_quantity_multiplier": %.2f,
    "martingale_premium_divisor": %.2f,
}

# Trading Hours Configuration
TRADING_HOURS = {
    "start_time": "%s",
    "end_time": "%s",
    "check_interval": %d,
}

# Holiday Configuration
HOLIDAYS = %s

# Logging Configuration
LOGGING_CONFIG = {
    "log_level": "%s",
    "log_file": "%s",
    "error_log_file": "%s",
}""" % (
        config["API_CONFIG"]["api_key"],
        config["API_CONFIG"]["api_url"],
        config["API_CONFIG"]["ws_url"],
        config["API_CONFIG"]["version"],
        
        config["INVESTMENT_CONFIG"]["base_investment"],
        config["INVESTMENT_CONFIG"]["lot_size"],
        config["INVESTMENT_CONFIG"]["lots_per_investment"],
        config["INVESTMENT_CONFIG"]["investment_per_lot"],
        
        config["STRATEGY_CONFIG"]["target_monthly_return"],
        config["STRATEGY_CONFIG"]["leg_premium_target"],
        config["STRATEGY_CONFIG"]["strangle_distance"],
        config["STRATEGY_CONFIG"]["sell_expiry_weeks"],
        config["STRATEGY_CONFIG"]["hedge_expiry_weeks"],
        config["STRATEGY_CONFIG"]["stop_loss_trigger"],
        config["STRATEGY_CONFIG"]["stop_loss_percentage"],
        config["STRATEGY_CONFIG"]["martingale_trigger"],
        config["STRATEGY_CONFIG"]["martingale_quantity_multiplier"],
        config["STRATEGY_CONFIG"]["martingale_premium_divisor"],
        
        config["TRADING_HOURS"]["start_time"],
        config["TRADING_HOURS"]["end_time"],
        config["TRADING_HOURS"]["check_interval"],
        
        str(config["HOLIDAYS"]),
        
        config["LOGGING_CONFIG"]["log_level"],
        config["LOGGING_CONFIG"]["log_file"],
        config["LOGGING_CONFIG"]["error_log_file"]
    )
    
    with open(config_path, 'w') as f:
        f.write(content)

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
        st.markdown("<p class='status-inactive'>● INACTIVE</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.subheader("Controls")
    if st.session_state.strategy_running:
        if st.button("Stop Strategy", key="stop_button"):
            if data_bridge.stop_strategy():
                st.session_state.strategy_running = False
                st.success("Strategy stopped successfully!")
                st.experimental_rerun()
    else:
        if st.button("Start Strategy", key="start_button"):
            if data_bridge.start_strategy():
                st.session_state.strategy_running = True
                st.success("Strategy started successfully!")
                st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.subheader("Emergency Actions")
    if st.button("Close All Positions", key="close_positions_button"):
        if data_bridge.close_all_positions():
            st.success("All positions closed successfully!")
            st.experimental_rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Tabs for different sections
tab1, tab2, tab3, tab4 = st.tabs(["Positions & P&L", "Strategy Configuration", "Logs & Monitoring", "About"])

# Tab 1: Positions & P&L
with tab1:
    st.markdown("<h2 class='sub-header'>Current Positions</h2>", unsafe_allow_html=True)
    
    # Load positions
    positions = data_bridge.get_positions()
    
    # Display positions
    if not positions.empty:
        st.dataframe(positions, use_container_width=True)
    else:
        st.info("No positions found.")
    
    st.markdown("<h2 class='sub-header'>P&L Performance</h2>", unsafe_allow_html=True)
    
    # Load P&L history
    pnl_history = data_bridge.get_pnl_history()
    
    # Display P&L charts
    if not pnl_history.empty:
        # Convert date column to datetime
        pnl_history['date'] = pd.to_datetime(pnl_history['date'])
        
        # Create two columns for charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily P&L chart
            fig = px.bar(
                pnl_history, 
                x='date', 
                y='daily_pnl',
                title='Daily P&L',
                labels={'date': 'Date', 'daily_pnl': 'Daily P&L'},
                color='daily_pnl',
                color_continuous_scale=['red', 'green'],
                color_continuous_midpoint=0
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Cumulative P&L chart
            fig = px.line(
                pnl_history, 
                x='date', 
                y='cumulative_pnl',
                title='Cumulative P&L',
                labels={'date': 'Date', 'cumulative_pnl': 'Cumulative P&L'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        # P&L metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Today's P&L", f"₹{pnl_history['daily_pnl'].iloc[-1]:,.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Total P&L", f"₹{pnl_history['cumulative_pnl'].iloc[-1]:,.2f}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            config = load_config()
            investment = config["INVESTMENT_CONFIG"]["base_investment"]
            monthly_return = pnl_history['cumulative_pnl'].iloc[-1] / investment * 100
            st.metric("Monthly Return", f"{monthly_return:.2f}%")
            st.markdown("</div>", unsafe_allo
(Content truncated due to size limit. Use line ranges to read in chunks)