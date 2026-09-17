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

# Compact, Flat, Theme-Responsive Editorial CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.2rem; padding-bottom: 1rem; max-width: 1400px; }

h1 { font-size: 1.6rem !important; font-weight: 700 !important; margin-bottom: 0px !important; }
[data-testid="stCaptionContainer"] p { font-size: 0.8rem !important; margin-bottom: 10px !important; }

/* ---- Compact KPI cards ---- */
.metric-card {
    background-color: var(--secondary-background-color);
    border: 1px solid var(--text-color);
    border-radius: 0px;
    padding: 12px 14px;
    min-height: 100px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.metric-label { font-family: 'Inter', sans-serif; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; opacity: 0.7; }
.metric-value { font-family: 'Inter', sans-serif; font-size: 1.6rem; font-weight: 700; line-height: 1.1; margin: 4px 0; }
.metric-sub { font-family: 'Inter', sans-serif; font-size: 0.65rem; opacity: 0.6; }

/* ---- Compact Recommendation block ---- */
.insight-card {
    background-color: var(--text-color);
    color: var(--background-color);
    border: 1px solid var(--text-color);
    border-radius: 0px;
    padding: 12px 18px;
    margin-top: 10px;
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 15px;
}
.insight-tag { font-family: 'IBM Plex Mono', monospace; font-size: 0.6rem; text-transform: uppercase; font-weight: 600; white-space: nowrap; }
.insight-body { font-size: 0.9rem; line-height: 1.3; flex-grow: 1; }
.insight-body strong { font-weight: 700; }

/* ---- Compact Chart Containers ---- */
.chart-container {
    background-color: transparent;
    border: 1px solid var(--text-color);
    padding: 10px;
    margin-bottom: 15px;
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
            's3', endpoint_url=R2_ENDPOINT, aws_access_key_id=R2_ACCESS_KEY, aws_secret_access_key=R2_SECRET_KEY, region_name='auto'
        )
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=FILE_NAME)
        df = pd.read_csv(io.BytesIO(response['Body'].read()), low_memory=False)
        df.to_csv(LOCAL_FILE, index=False)
        return df, "Live Cloud Data"
    except Exception:
        if os.path.exists(LOCAL_FILE): return pd.read_csv(LOCAL_FILE, low_memory=False), "Offline Mode (Local Cache)"
        else: return pd.DataFrame(), "Connection Error"

df, status = load_data()

# ==============================================================================
# SIDEBAR FILTERS
# ==============================================================================
with st.sidebar:
    st.title("Market Filters")
    st.caption(f"System State: **{status}**")
    st.markdown("---")
    
    if not df.empty:
        if not pd.api.types.is_datetime64_any_dtype(df['date']): df['date'] = pd.to_datetime(df['date'])
        
        all_commodities = sorted(df['commodity'].dropna().unique())
        selected_commodity = st.selectbox("Select Commodity:", all_commodities, index=all_commodities.index("Maize (white)") if "Maize (white)" in all_commodities else 0)
        
        all_markets = sorted(df['market'].dropna().unique())
        selected_markets = st.multiselect("Comparison Markets:", options=all_markets, default=[m for m in ["Techiman", "Sunyani", "Kintampo"] if m in all_markets] or all_markets[:3])
    else:
        st.error("No dataset available.")

# App Header
st.title("Ghana Commodity Market Intelligence")
st.caption("Strategic price surveillance, seasonality patterns, and arbitrage tracking for Techiman hub.")

if not df.empty:
    techiman_df = df[(df['market'].str.contains('Techiman', case=False, na=False)) & (df['commodity'] == selected_commodity) & (df['pricetype'] == 'Retail')].sort_values('date')

    # ==============================================================================
    # Augustine Abdulai: TOP-ROW KPIS, CONFIDENCE METRICS & RECOMMENDATIONS
    # ==============================================================================
    col1, col2, col3, col4 = st.columns(4)
    
    # **PLACE YOUR CODE HERE** (Augustine Abdulai: Update these KPI calculations)
    latest_price = techiman_df['price'].iloc[-1] if not techiman_df.empty else 0.0
    prev_price = techiman_df['price'].iloc[-2] if len(techiman_df) > 1 else latest_price
    mom_change = ((latest_price - prev_price) / prev_price * 100) if prev_price != 0 else 0.0
    confidence_pct = (techiman_df['is_actual_observation'].mean()) * 100 if 'is_actual_observation' in techiman_df.columns else 34.0

    overall_avg = df[(df['commodity'] == selected_commodity) & (df['pricetype'] == 'Retail')]['price'].mean()
    techiman_avg = techiman_df['price'].mean() if not techiman_df.empty else 0
    premium_pct = ((techiman_avg - overall_avg) / overall_avg) * 100 if techiman_avg and overall_avg else 0

    if premium_pct > 5: trend_text = f"Techiman historically pays <strong>{premium_pct:.0f}% more</strong> than national average for {selected_commodity}. Local sales favored."
    elif premium_pct < -5: trend_text = f"Techiman historically pays <strong>{abs(premium_pct):.0f}% less</strong> than national average for {selected_commodity}. Check comparisons."
    else: trend_text = f"Techiman's {selected_commodity} prices track closely to the national average (±5%)."

    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Latest Price</div><div class="metric-value">GH₵ {latest_price:,.2f}</div><div class="metric-sub">{selected_commodity}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Period Delta</div><div class="metric-value">{mom_change:+.1f}%</div><div class="metric-sub">Retail price, per KG</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Data Confidence</div><div class="metric-value">{confidence_pct:.0f}%</div><div class="metric-sub">Direct Field Obs.</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Market Role</div><div class="metric-value">Transit Hub</div><div class="metric-sub">Techiman Basin</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="insight-card"><div class="insight-tag">Advisory</div><div class="insight-body">{trend_text}</div></div>', unsafe_allow_html=True)

    # ==============================================================================
    # GRID VISUALIZATION LAYOUT (COMPACT)
    # ==============================================================================
    
    # ------------------- ROW 1 -------------------
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
        # ------------------------------------------------------------------------------
        # TAB 1: HISTORICAL PRICE TREND
        # ------------------------------------------------------------------------------
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("<h6 style='margin:0; font-weight:600;'>Longitudinal Trend</h6>", unsafe_allow_html=True)
        if not techiman_df.empty:
            fig_trend = px.line(techiman_df, x='date', y='price', labels={'price': 'Price (GH₵)', 'date': 'Date'})
            fig_trend.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified")
            st.plotly_chart(fig_trend, use_container_width=True, theme="streamlit")
        st.markdown('</div>', unsafe_allow_html=True)

    with row1_col2:
        # ------------------------------------------------------------------------------
        # TAB 2: Joseph Mensah — SEASONAL TREND ENGINE
        # ------------------------------------------------------------------------------
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("<h6 style='margin:0; font-weight:600;'>Seasonal Price Index</h6>", unsafe_allow_html=True)
        
        # **PLACE YOUR CODE HERE** (Joseph Mensah)
        season_df = techiman_df.copy()
        season_df['month'] = season_df['date'].dt.strftime('%b')
        monthly_avg = season_df.groupby('month')['price'].mean().reindex(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']).reset_index()

        fig_season = px.bar(monthly_avg, x='month', y='price', labels={'month': '', 'price': 'Price (GH₵)'})
        fig_season.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_season, use_container_width=True, theme="streamlit")
        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------- ROW 2 -------------------
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        # ------------------------------------------------------------------------------
        # TAB 3: Lidwan Abubakari — MARKET COMPARISON & ARBITRAGE
        # ------------------------------------------------------------------------------
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("<h6 style='margin:0; font-weight:600;'>Regional Comparison</h6>", unsafe_allow_html=True)
        
        # **PLACE YOUR CODE HERE** (Lidwan Abubakari)
        comp_df = df[(df['commodity'] == selected_commodity) & (df['market'].isin(selected_markets))]
        market_summary = comp_df.groupby('market')['price'].mean().reset_index()
        
        fig_market = px.bar(market_summary, x='market', y='price', color='market', labels={'market': '', 'price': 'Price (GH₵)'})
        fig_market.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), showlegend=False)
        st.plotly_chart(fig_market, use_container_width=True, theme="streamlit")
        st.markdown('</div>', unsafe_allow_html=True)

    with row2_col2:
        # ------------------------------------------------------------------------------
        # TAB 4: Hanna Oduro — WHOLESALE VS. RETAIL SPREAD
        # ------------------------------------------------------------------------------
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown("<h6 style='margin:0; font-weight:600;'>Wholesale vs. Retail Spread</h6>", unsafe_allow_html=True)
        
                # **PLACE YOUR CODE HERE** (Hanna Oduro)
        # Filter to Techiman + selected commodity, both price types included
        spread_source = df[
            (df['market'].str.contains('Techiman', case=False, na=False)) &
            (df['commodity'] == selected_commodity)
        ]

        # Pivot Wholesale/Retail into side-by-side columns per date
        spread_pivot = spread_source.pivot_table(
            index='date',
            columns='pricetype',
            values='price_per_kg',
            aggfunc='mean'
        ).reset_index()

        has_both = 'Wholesale' in spread_pivot.columns and 'Retail' in spread_pivot.columns

        if has_both:
            # Keep only dates where BOTH wholesale and retail exist
            spread_pivot = spread_pivot.dropna(subset=['Wholesale', 'Retail']).sort_values('date')
            spread_pivot['markup'] = spread_pivot['Retail'] - spread_pivot['Wholesale']

        if has_both and not spread_pivot.empty:
            fig_markup = px.line(
                spread_pivot, x='date', y='markup',
                labels={'markup': 'Markup (GH₵/kg)', 'date': ''}
            )
            fig_markup.add_hline(y=0, line_dash="dot", line_color="gray")
            fig_markup.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), hovermode="x unified")
            st.plotly_chart(fig_markup, use_container_width=True, theme="streamlit")
        else:
            st.info("No matched wholesale/retail pairs available for this commodity at Techiman.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------- ROW 3 (Full Width) -------------------
    # ------------------------------------------------------------------------------
    # TAB 5: Lydia Oduro — COMMODITY VOLATILITY & RISK MATRIX
    # ------------------------------------------------------------------------------
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("<h6 style='margin:0; font-weight:600;'>Price Volatility & Market Risk Ranking</h6>", unsafe_allow_html=True)

    # **PLACE YOUR CODE HERE** (Lydia Oduro)
    risk_df = df.dropna(subset=['price_per_kg'])
    volatility_summary = risk_df.groupby('commodity')['price_per_kg'].agg(mean_price='mean', std_price='std', n='count').reset_index()
    volatility_summary = volatility_summary[volatility_summary['n'] >= 12]
    volatility_summary['cv'] = volatility_summary['std_price'] / volatility_summary['mean_price']
    volatility_summary = volatility_summary.sort_values('cv', ascending=True).tail(10)

    fig_risk = px.bar(volatility_summary, x='cv', y='commodity', orientation='h', labels={'cv': 'Volatility (Std Dev / Mean)', 'commodity': ''})
    fig_risk.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig_risk, use_container_width=True, theme="streamlit")
    st.markdown('</div>', unsafe_allow_html=True)