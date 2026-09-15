import streamlit as st
import pandas as pd
import boto3
import io
import os

# 1. Setup Page
st.set_page_config(page_title="Techiman Market Dashboard", layout="wide")

# 2. Securely pull credentials from Streamlit Secrets
R2_ACCESS_KEY = st.secrets["R2_ACCESS_KEY_ID"]
R2_SECRET_KEY = st.secrets["R2_SECRET_ACCESS_KEY"]
R2_ENDPOINT = st.secrets["R2_ENDPOINT_URL"]
BUCKET_NAME = "amalitech-capstone-data1"
FILE_NAME = "clean/wfp_gha_clean.csv" # This is the clean version of the data
LOCAL_FILE = "offline_wfp_data.csv"

# 3. The Offline-First Data Loader
@st.cache_data(ttl=3600)  # Caches data for 1 hour to prevent constant cloud downloads
def load_data():
    """Attempts to fetch from Cloudflare R2, falls back to local CSV if offline."""
    try:
        # Try to connect to the cloud
        s3_client = boto3.client(
            's3',
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            region_name='auto'
        )
        
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
        csv_content = response['Body'].read()
        df = pd.read_csv(io.BytesIO(csv_content), low_memory=False)
        
        # Save a fresh local copy for offline use
        df.to_csv(LOCAL_FILE, index=False)
        
        return df, "🟢 Live Cloud Data"
        
    except Exception as e:
        # If internet is down, load the local backup copy
        if os.path.exists(LOCAL_FILE):
            df = pd.read_csv(LOCAL_FILE, low_memory=False)
            return df, "🟡 Offline Mode (Local Backup)"
        else:
            st.error("No internet connection and no local backup found.")
            return pd.DataFrame(), "🔴 Error"

# 4. Build the Dashboard UI
st.title("Techiman Market Price Tracker")

# Load the data and display connection status
df, status = load_data()
st.caption(f"Connection Status: {status}")

if not df.empty:
    # Filter the dataset specifically for the Techiman market
    techiman_df = df[df['market'].str.contains('Techiman', case=False, na=False)]
    
    # Create a dropdown to select a commodity
    commodity_list = sorted(techiman_df['commodity'].unique())
    selected_commodity = st.selectbox("Select a Commodity:", commodity_list)
    
    # Filter down to the selected commodity and plot it
    plot_data = techiman_df[techiman_df['commodity'] == selected_commodity]
    
    st.subheader(f"Historical Price Trend for {selected_commodity}")
    
    # A simple native Streamlit line chart to meet the Gate 2 requirement
    st.line_chart(plot_data.set_index('date')['price'])