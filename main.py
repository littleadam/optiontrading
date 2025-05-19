import os
import sys
import streamlit as st

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# This is the main entry point for Flask deployment
def main():
    # Import the app module
    from app import data_bridge
    
    # Set page configuration
    st.set_page_config(
        page_title="Nifty 50 Trading Dashboard",
        page_icon="📈",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Run the app
    import app

if __name__ == "__main__":
    main()
