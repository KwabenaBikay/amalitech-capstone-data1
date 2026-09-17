import streamlit as st
import pandas as pd
import plotly.express as px
import boto3
import io
import os

# ==============================================================================
# TEAM LEAD: BISMARK — ARCHITECTURE & PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Techiman Market Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Flat, high-contrast editorial design styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background-color: #FAF9F6; }
.block-container { padding-top: 2.5rem; padding-bottom: 3rem; max-width: 1400px; }

h1 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    font-size: 2.1rem !important;
    letter-spacing: -0.025em !important;
    color: #111111 !important;
}
h2, h3 {
    font-family: 'Inter', sans-serif !important;
    color: #111111 !important;
    font-weight: 600 !important;
    letter-spacing: -0.015em !important;
}
[data-testid="stCaptionContainer"] p {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    color: #6E6E6E !important;
}

/* ---- KPI cards ---- */
.metric-card {
    background-color: #FFFFFF;
    border: 1px solid #111111;
    border-radius: 0;
    padding: 20px 22px;
    min-height: 150px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.metric-label {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #6E6E6E;
    font-weight: 500;
}
.metric-value {
    font-family: 'Inter', sans-serif;
    font-size: 2.1rem;
    font-weight: 600;
    color: #111111;
    line-height: 1;
    letter-spacing: -0.03em;
}
.metric-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.78rem;
    color: #8A8A8A;
}

/* ---- Recommendation: inverted block ---- */
.insight-card {
    background-color: #111111;
    border: 1px solid #111111;
    border-radius: 0;
    padding: 26px 30px;
    margin-top: 28px;
    margin-bottom: 30px;
}
.insight-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.66rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    color: #8A8A8A;
    font-weight: 500;
    margin-bottom: 12px;
}
.insight-body {
    font-family: 'Inter', sans-serif;
    font-size: 1.1rem;
    font-weight: 500;
    color: #FAF9F6;
    line-height: 1.55;
}
.insight-body strong { color: #FFFFFF; font-weight: 700; }
.insight-note {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #8A8A8A;
    margin-top: 16px;
    line-height: 1.5;
}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 28px;
    border-bottom: 1px solid #DDDAD2;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif;
    font-size: 0.88rem;
    font-weight: 500;
    color: #111111 !important;
    padding: 10px 0;
    opacity: 1 !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #111111 !important;
    opacity: 1 !important;
}
.stTabs [aria-selected="true"] {
    color: #111111 !important;
    font-weight: 700 !important;
}
.stTabs [data-baseweb="tab-highlight"] {
    background-color: #111111 !important;
}



/* ---- Sidebar: black panel ---- */
/* Multiselect chips - forced */
section[data-testid="stSidebar"] span[data-baseweb="tag"],
section[data-testid="stSidebar"] span[data-baseweb="tag"] > div,
section[data-testid="stSidebar"] div[data-baseweb="tag"] {
    background-color: #FFFFFF !important;
    background: #FFFFFF !important;
    border-radius: 0 !important;
    border: none !important;
}
section[data-testid="stSidebar"] span[data-baseweb="tag"] *,
section[data-testid="stSidebar"] div[data-baseweb="tag"] * {
    color: #111111 !important;
    fill: #111111 !important;
}

/* Collapse button - all variants */
[data-testid="stSidebarCollapseButton"],
[data-testid="baseButton-headerNoPadding"],
[data-testid="stSidebarCollapsedControl"] {
    background-color: transparent !important;
}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapseButton"] svg path,
[data-testid="baseButton-headerNoPadding"] svg,
[data-testid="baseButton-headerNoPadding"] svg path,
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapsedControl"] svg path {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
    stroke: #FFFFFF !important;
    opacity: 1 !important;
}
section[data-testid="stSidebar"] button svg,
section[data-testid="stSidebar"] button svg path {
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}
</style>
""", unsafe_allow_html=True)

# Cloudflare R2 Credentials & Paths
R2_ACCESS_KEY = st.secrets["R2_ACCESS_KEY_ID"]
R2_SECRET_KEY = st.secrets["R2_SECRET_ACCESS_KEY"]
R2_ENDPOINT = st.secrets["R2_ENDPOINT_URL"]
BUCKET_NAME = "amalitech-capstone-data1"
FILE_NAME = "clean/wfp_gha_clean.csv"
LOCAL_FILE = "offline_wfp_data.csv"

# ==============================================================================
# TEAM LEAD: BISMARK — OFFLINE-FIRST DATA PIPELINE
# ==============================================================================
@st.cache_data(ttl=3600)
def load_data():
    """Fetches cleaned data from Cloudflare R2 with offline fallback."""
    try:
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
        
        df.to_csv(LOCAL_FILE, index=False)
        return df, "Live Cloud Data"
        
    except Exception:
        if os.path.exists(LOCAL_FILE):
            df = pd.read_csv(LOCAL_FILE, low_memory=False)
            return df, "Offline Mode (Local Cache)"
        else:
            return pd.DataFrame(), "Connection Error"

df, status = load_data()

# ==============================================================================
# SIDEBAR FILTERS & CONTROLS (SHARED WORKSPACE)
# ==============================================================================
with st.sidebar:
    st.title("Market Filters")
    st.caption(f"System State: **{status}**")
    st.markdown("---")
    
    if not df.empty:
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        all_commodities = sorted(df['commodity'].dropna().unique())
        default_index = all_commodities.index("Maize (white)") if "Maize (white)" in all_commodities else 0
        selected_commodity = st.selectbox("Select Commodity:", all_commodities, index=default_index)
        
        all_markets = sorted(df['market'].dropna().unique())
        default_markets = [m for m in ["Techiman", "Sunyani", "Kintampo"] if m in all_markets]
        selected_markets = st.multiselect(
            "Comparison Markets:", 
            options=all_markets, 
            default=default_markets if default_markets else all_markets[:3]
        )
        
        min_date = df['date'].min().to_pydatetime()
        max_date = df['date'].max().to_pydatetime()
        selected_date_range = st.date_input("Date Range:", value=(min_date, max_date))
    else:
        st.error("No dataset available.")

# App Header
st.title("Ghana Commodity Market Intelligence")
st.caption("Strategic price surveillance, seasonality patterns, and arbitrage tracking for Techiman hub.")

if not df.empty:
    techiman_df = df[(df['market'].str.contains('Techiman', case=False, na=False)) & 
                     (df['commodity'] == selected_commodity) &
                     (df['pricetype'] == 'Retail')].sort_values('date')
       

    # ==============================================================================
    # Augustine Abdulai: TOP-ROW KPIS, CONFIDENCE METRICS & RECOMMENDATIONS
    # ==============================================================================
    col1, col2, col3, col4 = st.columns(4)
    
        # **PLACE YOUR CODE HERE** (Augustine Abdulai: Update these KPI calculations)
    latest_price = techiman_df['price'].iloc[-1] if not techiman_df.empty else 0.0
    prev_price = techiman_df['price'].iloc[-2] if len(techiman_df) > 1 else latest_price
    mom_change = ((latest_price - prev_price) / prev_price * 100) if prev_price != 0 else 0.0
    confidence_pct = (techiman_df['is_actual_observation'].mean()) * 100 if 'is_actual_observation' in techiman_df.columns else 34.0

    # Compare Techiman against the national average for this commodity
    overall_avg = df[(df['commodity'] == selected_commodity) &
                     (df['pricetype'] == 'Retail')]['price'].mean()
    techiman_avg = techiman_df['price'].mean() if not techiman_df.empty else 0

    if techiman_avg and overall_avg:
        premium_pct = ((techiman_avg - overall_avg) / overall_avg) * 100
    else:
        premium_pct = 0

    if premium_pct > 5:
        trend_text = (f"Techiman has historically paid <strong>{premium_pct:.0f}% more</strong> than the "
                      f"national average for {selected_commodity}. Selling locally has generally been "
                      f"the stronger option.")
    elif premium_pct < -5:
        trend_text = (f"Techiman has historically paid <strong>{abs(premium_pct):.0f}% less</strong> than the "
                      f"national average for {selected_commodity}. Check the Market Comparison tab before "
                      f"committing to a local sale.")
    else:
        trend_text = (f"Techiman's {selected_commodity} prices have historically tracked close to the "
                      f"national average, within 5% either way.")

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Latest Techiman Price</div>
            <div class="metric-value">GH₵ {latest_price:,.2f}</div>
            <div class="metric-sub">{selected_commodity}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        delta_color = "#D9381E" if mom_change < 0 else "#2E7D32"
        st.markdown(f"""
        <div class="metric-card">
             <div class="metric-label">Change Since Last Reading</div>
            <div class="metric-value" style="color: {delta_color};">{mom_change:+.1f}%</div>
            <div class="metric-sub">Retail price, per KG</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Data Confidence Score</div>
            <div class="metric-value">{confidence_pct:.0f}%</div>
            <div class="metric-sub">Direct Field Observations</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Market Role</div>
            <div class="metric-value">Transit Hub</div>
            <div class="metric-sub">Techiman Central Basin</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-tag">Recommendation</div>
        <div class="insight-body">
            {trend_text}
        </div>
        <div class="insight-note">
            Historical data spans 2006 to mid-2023. Insights reflect persistent seasonal
            patterns, not live spot quotes.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ==============================================================================
    # TABBED VISUALIZATION LAYOUT
    # ==============================================================================
    tab_trend, tab_season, tab_market, tab_markup, tab_risk = st.tabs([
        "Price History",
        "Seasonality Curve",
        "Market Comparison",
        "Wholesale vs Retail",
        "Commodity Volatility"
    ])

    # ------------------------------------------------------------------------------
    # TAB 1: HISTORICAL PRICE TREND
    # ------------------------------------------------------------------------------
    with tab_trend:
        st.subheader(f"Longitudinal Price Trend: {selected_commodity}")
        if not techiman_df.empty:
            fig_trend = px.line(
                techiman_df, 
                x='date', 
                y='price',
                title=f"{selected_commodity} Price History in Techiman (GH₵)",
                labels={'price': 'Price (GH₵)', 'date': 'Observation Date'},
                template="simple_white"
            )
            fig_trend.update_traces(line=dict(color='#111111', width=2))
            fig_trend.update_layout(hovermode="x unified")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No historical records available for this commodity in Techiman.")

    # ------------------------------------------------------------------------------
    # TAB 2: Joseph Mensah — SEASONAL TREND ENGINE
    # ------------------------------------------------------------------------------
    with tab_season:
        st.subheader("Seasonal Price Index (17-Year Aggregates)")
        st.caption("Identifies regular annual harvest peaks and lean season troughs by month.")
        
        # **PLACE YOUR CODE HERE** (Joseph Mensah)
        season_df = techiman_df.copy()
        season_df['month'] = season_df['date'].dt.strftime('%b')
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_avg = season_df.groupby('month')['price'].mean().reindex(month_order).reset_index()

        fig_season = px.bar(
            monthly_avg,
            x='month',
            y='price',
            labels={'month': 'Month', 'price': 'Historical Mean Price (GH₵)'},
            template="simple_white"
        )
        fig_season.update_traces(marker_color='#333333')
        st.plotly_chart(fig_season, use_container_width=True)

    # ------------------------------------------------------------------------------
    # TAB 3: Lidwan Abubakari — MARKET COMPARISON & ARBITRAGE
    # ------------------------------------------------------------------------------
    with tab_market:
        st.subheader("Regional Market Price Comparison")
        st.caption("Evaluates selling opportunities between Techiman and neighbouring regional trading hubs.")
        
        # **PLACE YOUR CODE HERE** (Lidwan Abubakari)
        comp_df = df[(df['commodity'] == selected_commodity) & (df['market'].isin(selected_markets))]
        market_summary = comp_df.groupby('market')['price'].mean().reset_index()
        
        fig_market = px.bar(
            market_summary,
            x='market',
            y='price',
            color='market',
            labels={'market': 'Trading Hub', 'price': 'Mean Price (GH₵)'},
            template="simple_white"
        )
        st.plotly_chart(fig_market, use_container_width=True)

    # ------------------------------------------------------------------------------
    # TAB 4: Hanna Oduro — WHOLESALE VS. RETAIL SPREAD
    # ------------------------------------------------------------------------------
    with tab_markup:
        st.subheader("Wholesale vs. Retail Spread Analysis")
        st.caption("Quantifies middleman margin by contrasting farmgate/wholesale price with end-consumer retail.")
        
        # **PLACE YOUR CODE HERE** (Hanna Oduro)
        if 'pricetype' in techiman_df.columns and len(techiman_df['pricetype'].unique()) > 1:
            fig_markup = px.line(
                techiman_df,
                x='date',
                y='price',
                color='pricetype',
                labels={'price': 'Price (GH₵)', 'date': 'Date', 'pricetype': 'Pricing Tier'},
                template="simple_white"
            )
            st.plotly_chart(fig_markup, use_container_width=True)
        else:
            st.info("Insufficient retail/wholesale price type pairs available for this commodity selection.")

    # ------------------------------------------------------------------------------
    # TAB 5: Lydia Oduro — COMMODITY VOLATILITY & RISK MATRIX
    # ------------------------------------------------------------------------------
    with tab_risk:
        st.subheader("Price Volatility & Market Risk Ranking")
        st.caption("Measures price stability across commodities to identify income predictability.")
        
        # **PLACE YOUR CODE HERE** (Lydia Oduro)
        all_techiman = df[df['market'].str.contains('Techiman', case=False, na=False)]
        volatility_summary = all_techiman.groupby('commodity')['price'].std().dropna().reset_index()
        volatility_summary = volatility_summary.sort_values(by='price', ascending=True).tail(10)
        
        fig_risk = px.bar(
            volatility_summary,
            x='price',
            y='commodity',
            orientation='h',
            labels={'price': 'Historical Std Dev (GH₵)', 'commodity': 'Commodity'},
            title="Top 10 Volatile Commodities in Techiman",
            template="simple_white"
        )
        fig_risk.update_traces(marker_color='#555555')
        st.plotly_chart(fig_risk, use_container_width=True)

else:
    st.warning("Awaiting valid dataset load. Please verify cloud credentials or local cache.")