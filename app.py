import streamlit as st
import pandas as pd
import plotly.express as px
import boto3
import io
import os

def clean_wholesale(data):
    data = data.dropna(subset=['price_per_kg'])
    data = data[data['pricetype'] == 'Wholesale'].sort_values('date').copy()
    data['recent_median'] = data.groupby('market')['price_per_kg'].transform(
        lambda s: s.shift(1).rolling(6, min_periods=3).median())
    keep = data['recent_median'].isna() | (data['price_per_kg'] <= data['recent_median'] * 3)
    return data[keep]

# ==============================================================================
# TEAM LEAD: BISMARK — ARCHITECTURE & PAGE CONFIGURATION
# ==============================================================================
st.set_page_config(
    page_title="Techiman Market Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Compact, Flat, High-Contrast Editorial CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.block-container { padding-top: 1.2rem; padding-bottom: 1rem; max-width: 1400px; }

h1 { font-size: 1.6rem !important; font-weight: 700 !important; margin-bottom: 0px !important; letter-spacing: -0.02em; }
[data-testid="stCaptionContainer"] p { font-size: 0.8rem !important; margin-bottom: 15px !important; }

/* ---- Flat, High-Contrast KPI cards ---- */
.metric-card {
    background-color: var(--secondary-background-color);
    border: 1px solid var(--text-color);
    border-radius: 0px !important;
    padding: 14px 16px;
    min-height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 2px 2px 0px 0px rgba(0,0,0,0.1);
}
.metric-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8; display: flex; align-items: center; gap: 6px; }
.metric-value { font-family: 'Inter', sans-serif; font-size: 1.7rem; font-weight: 700; line-height: 1.1; margin: 8px 0 4px 0; letter-spacing: -0.03em;}
.metric-sub { font-family: 'Inter', sans-serif; font-size: 0.7rem; opacity: 0.65; }

/* ---- Editorial Recommendation block (Long Rectangle) ---- */
.insight-card {
    background-color: var(--text-color);
    color: var(--background-color);
    border-radius: 0px !important;
    padding: 24px 28px;
    margin-top: 15px;
    margin-bottom: 25px;
    display: block;
}
.insight-tag { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; text-transform: uppercase; font-weight: 600; letter-spacing: 0.1em; opacity: 0.7; margin-bottom: 10px;}
.insight-body { font-size: 1.05rem; line-height: 1.4; font-weight: 500; }
.insight-body strong { font-weight: 700; }

/* ---- Compact Chart Containers ---- */
.chart-container {
    background-color: transparent;
    border: 1px solid var(--text-color);
    border-radius: 0px !important;
    padding: 12px;
    margin-bottom: 15px;
}
.chart-title { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }

/* 1. KPI cards forest green, white text, no top bars */
.metric-card {
    background-color: #FFFFFF;
    border: 1px solid #123D2B;
    border-radius: 6px !important;
    padding: 14px 16px;
    min-height: 110px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: none;
}
.metric-card.hero {
    background-color: #123D2B;
    border-color: #123D2B;
}
.metric-card.hero .metric-label,
.metric-card.hero .metric-value,
.metric-card.hero .metric-sub { color: #FFFFFF !important; }
.metric-card.hero .metric-sub { opacity: 0.7; }

.metric-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }

.metric-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    background-color: #A9E7BE;
    color: #0B2C1E;
    padding: 3px 8px;
    border-radius: 20px;
    white-space: nowrap;
}
.metric-label, .metric-sub { opacity: 0.75 !important; }

/* 3. Brand block */
.brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 0 16px 0;
    margin-top: -55px;
    border-bottom: 1px solid #DDD9D0;
    margin-bottom: 18px;
}
.brand-name { font-size: 1rem; font-weight: 700; color: #123D2B; letter-spacing: -0.01em; line-height: 1; }

/* 4. Collapse button always visible */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] button { opacity: 1 !important; }
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stSidebarCollapseButton"] svg path {
    fill: #123D2B !important;
    stroke: #123D2B !important;
    opacity: 1 !important;
}

/* 5. Select boxes forest green */
section[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #123D2B !important;
    border: 1px solid #123D2B !important;
    border-radius: 0 !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] > div * { color: #FFFFFF !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] svg { fill: #FFFFFF !important; }

/* 6. Faster sidebar collapse */
section[data-testid="stSidebar"] { transition: all 0.12s ease !important; }
section[data-testid="stSidebar"] > div { transition: none !important; }
section[data-testid="stSidebar"] { border-right: 1px solid #E5E7EB; }

.insight-card {
    background-color: #F4FAF6 !important;
    border: 1.5px solid #123D2B !important;
    border-radius: 6px !important;
    padding: 20px 24px !important;
}
.insight-card * { color: #123D2B !important; }
.insight-tag { color: #2E7D5B !important; opacity: 1 !important; }

.brand { position: relative; z-index: 1; }
[data-testid="stSidebarCollapseButton"] {
    position: relative;
    z-index: 999 !important;
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
    try:
        s3_client = boto3.client('s3', endpoint_url=R2_ENDPOINT, aws_access_key_id=R2_ACCESS_KEY, aws_secret_access_key=R2_SECRET_KEY, region_name='auto')
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
    st.markdown("""
    <div class="brand">
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="7" fill="#123D2B"/>
            <path d="M8 23C8 15.5 13 11 22 10C22 18.5 17 23 8 23Z" fill="#FFFFFF"/>
            <polyline points="11,20 14,17 17,18.5 21,13" stroke="#123D2B" stroke-width="1.6" fill="none" stroke-linecap="square"/>
        </svg>
        <div class="brand-name">AgriDash</div>
    </div>
    """, unsafe_allow_html=True)
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
    
    # **PLACE YOUR CODE HERE** (Augustine Abdulai)
    kpi_df = clean_wholesale(df[(df['market'].str.contains('Techiman', case=False, na=False)) &
                                (df['commodity'] == selected_commodity)])
    national_df = clean_wholesale(df[df['commodity'] == selected_commodity])

    has_data = len(kpi_df) > 0
    has_delta = len(kpi_df) > 1

    latest_price = kpi_df['price_per_kg'].iloc[-1] if has_data else 0.0
    prev_price = kpi_df['price_per_kg'].iloc[-2] if has_delta else latest_price
    mom_change = ((latest_price - prev_price) / prev_price * 100) if has_delta and prev_price else 0.0
    confidence_pct = kpi_df['is_actual_observation'].mean() * 100 if has_data else 0.0

    overall_avg = national_df['price_per_kg'].mean() if not national_df.empty else 0
    techiman_avg = kpi_df['price_per_kg'].mean() if has_data else 0

    if not has_data or not overall_avg:
        trend_text = (f"<strong>No wholesale records</strong> exist for {selected_commodity} "
                      f"in Techiman, so no pricing guidance can be given.")
    else:
        premium_pct = ((techiman_avg - overall_avg) / overall_avg) * 100
        if premium_pct > 5:
            trend_text = f"Techiman historically pays <strong>{premium_pct:.0f}% more</strong> than national average for {selected_commodity}. Local sales favored."
        elif premium_pct < -5:
            trend_text = f"Techiman historically pays <strong>{abs(premium_pct):.0f}% less</strong> than national average for {selected_commodity}. Check comparisons."
        else:
            trend_text = f"Techiman's {selected_commodity} prices track closely to the national average (±5%)."

        if confidence_pct < 25:
            trend_text = (f"<strong>Limited data.</strong> Only {confidence_pct:.0f}% of {selected_commodity} "
                          f"records were recorded at the market, so no reliable guidance can be given.")
        elif confidence_pct < 60:
            trend_text = f"<strong>Treat with caution.</strong> {trend_text} Only {confidence_pct:.0f}% of records are direct observations."
    # Forest green KPI cards, no colored top borders
    with col1:
        price_display = f"GH₵ {latest_price:,.2f}" if has_data else "No data"
        st.markdown(f'<div class="metric-card hero"><div class="metric-top"><div class="metric-label">Latest Price</div><div class="metric-tag">{selected_commodity}</div></div><div class="metric-value">{price_display}</div><div class="metric-sub">Wholesale price, per KG</div></div>', unsafe_allow_html=True)
    with col2:
        if has_delta:
            delta_color = "#D9381E" if mom_change < 0 else "#2E7D32"
            delta_tag = "Down" if mom_change < 0 else "Up"
            delta_display = f"{mom_change:+.1f}%"
        else:
            delta_color, delta_tag, delta_display = "#9A9A9A", "N/A", "—"
        st.markdown(f'<div class="metric-card"><div class="metric-top"><div class="metric-label">Period Delta</div><div class="metric-tag">{delta_tag}</div></div><div class="metric-value" style="color: {delta_color};">{delta_display}</div><div class="metric-sub">Since last reading</div></div>', unsafe_allow_html=True)
    with col3:
        conf_tag = "Low" if confidence_pct < 25 else ("Medium" if confidence_pct < 60 else "High")
        st.markdown(f'<div class="metric-card"><div class="metric-top"><div class="metric-label">Data Confidence</div><div class="metric-tag">{conf_tag}</div></div><div class="metric-value">{confidence_pct:.0f}%</div><div class="metric-sub">Direct field obs.</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-top"><div class="metric-label">Market Role</div><div class="metric-tag">Bono East</div></div><div class="metric-value">Transit Hub</div><div class="metric-sub">Techiman Basin</div></div>', unsafe_allow_html=True)
    # Sharp, editorial advisory block (Long Rectangle)
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-tag">Strategic Advisory</div>
        <div class="insight-body">{trend_text}</div>
    </div>
    """, unsafe_allow_html=True)

    # ==============================================================================
    # GRID VISUALIZATION LAYOUT (COMPACT)
    # ==============================================================================
    
    # ------------------- ROW 1 -------------------
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
        # ------------------------------------------------------------------------------
        # TAB 1: HISTORICAL PRICE TREND
        # ------------------------------------------------------------------------------
        st.markdown('<div class="chart-container"><div class="chart-title">Longitudinal Trend</div>', unsafe_allow_html=True)
        if not techiman_df.empty:
            fig_trend = px.line(techiman_df, x='date', y='price', labels={'price': 'Price (GH₵)', 'date': 'Date'})
            fig_trend.update_traces(line=dict(color='#111111', width=2))
            fig_trend.update_layout(height=280, margin=dict(l=50, r=20, t=10, b=40), hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_trend, use_container_width=True, theme=None)
        st.markdown('</div>', unsafe_allow_html=True)

    with row1_col2:
        # ------------------------------------------------------------------------------
        # TAB 2: Joseph Mensah — SEASONAL TREND ENGINE
        # ------------------------------------------------------------------------------
        st.markdown('<div class="chart-container"><div class="chart-title">Seasonal Price Index</div>', unsafe_allow_html=True)
        
        # **PLACE YOUR CODE HERE** (Joseph Mensah)
        selected_commodity = "Maize"
        commodity_df = df[df["commodity"] == selected_commodity].copy()

        monthly_average = (
            commodity_df
                .groupby(["month", "month_name"], as_index=False)["price"]
                .mean()
                .sort_values("month")
        )

        fig_season = px.line(
            monthly_average,
            x="month_name",
            y="price",
            title=f"Historical Price Patern - {selected_commodity}",
            labels={
                "month_name": "Month",
                "price": "Average Historical Price (GH₵)"
            }
        )

        fig_season.show()
        fig_season.update_traces(line=dict(color='#111111', width=2))
        fig_season.update_layout(height=280, margin=dict(l=50, r=20, t=40, b=40), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_season, use_container_width=True, theme=None)
        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------- ROW 2 -------------------
    row2_col1, row2_col2 = st.columns(2)

    with row2_col1:
        # ------------------------------------------------------------------------------
        # TAB 3: Lidwan Abubakari — MARKET COMPARISON & ARBITRAGE
        # ------------------------------------------------------------------------------
        st.markdown('<div class="chart-container"><div class="chart-title">Regional Comparison</div>', unsafe_allow_html=True)
        
        # **PLACE YOUR CODE HERE** (Lidwan Abubakari)
        period_choice = st.radio("Time period:", ["Last 3M", "Last 6M", "Last 12M", "All Time"], index=2, horizontal=True, key="tab3_period")
        comp_df = df[(df['commodity'] == selected_commodity) & (df['market'].isin(selected_markets))].copy()

        if not comp_df.empty:
            max_date = comp_df['date'].max()
            period_map = {"Last 3M": 3, "Last 6M": 6, "Last 12M": 12, "All Time": None}
            months = period_map[period_choice]
            if months is not None: comp_df = comp_df[comp_df['date'] >= max_date - pd.DateOffset(months=months)]

        if not comp_df.empty and 'pricetype' in comp_df.columns:
            market_summary = comp_df.groupby(['market', 'pricetype'])['price'].agg(['mean', 'min', 'max', 'count']).reset_index().rename(columns={'mean': 'average_price', 'min': 'lowest_price', 'max': 'highest_price', 'count': 'observations'})
            if not market_summary.empty:
                retail_only = market_summary[market_summary['pricetype'].str.lower() == 'retail']
                market_order = retail_only.groupby('market')['average_price'].mean().sort_values(ascending=True).index.tolist() if not retail_only.empty else sorted(market_summary['market'].unique())
                
                if not retail_only.empty:
                    retail_sorted = retail_only.sort_values('average_price', ascending=True)
                    cheapest = retail_sorted.iloc[0]
                    expensive = retail_sorted.iloc[-1]
                    diff = expensive['average_price'] - cheapest['average_price']
                    pct = (diff / cheapest['average_price'] * 100) if cheapest['average_price'] != 0 else 0
                    
                    if len(retail_sorted) > 1:
                        st.markdown(f"<div style='font-size:0.8rem; margin-bottom:10px;'><strong>Arbitrage Spread:</strong> {cheapest['market']} (GH₵ {cheapest['average_price']:,.2f}) vs {expensive['market']} (GH₵ {expensive['average_price']:,.2f}) &rarr; <strong>+{pct:.1f}% Margin</strong></div>", unsafe_allow_html=True)
                
                fig_market = px.bar(market_summary, x='market', y='average_price', color='pricetype', barmode='group', text='average_price', labels={'market': '', 'average_price': 'Avg Price (GH₵)', 'pricetype': ''}, category_orders={'market': market_order}, color_discrete_sequence=['#111111', '#9A9A9A'])
                fig_market.update_layout(height=230, margin=dict(l=50, r=20, t=10, b=40), legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_market, use_container_width=True, theme=None)
        st.markdown('</div>', unsafe_allow_html=True)

    with row2_col2:
        # ------------------------------------------------------------------------------
        # TAB 4: Hanna Oduro — WHOLESALE VS. RETAIL SPREAD
        # ------------------------------------------------------------------------------
        st.markdown('<div class="chart-container"><div class="chart-title">Wholesale vs. Retail Spread</div>', unsafe_allow_html=True)
        
        # **PLACE YOUR CODE HERE** (Hanna Oduro)
        spread_source = df[(df['market'].str.contains('Techiman', case=False, na=False)) & (df['commodity'] == selected_commodity)]
        spread_pivot = spread_source.pivot_table(index='date', columns='pricetype', values='price_per_kg', aggfunc='mean').reset_index()

        has_both = 'Wholesale' in spread_pivot.columns and 'Retail' in spread_pivot.columns
        if has_both:
            spread_pivot = spread_pivot.dropna(subset=['Wholesale', 'Retail']).sort_values('date')
            spread_pivot['markup'] = spread_pivot['Retail'] - spread_pivot['Wholesale']

        if has_both and not spread_pivot.empty:
            fig_markup = px.line(spread_pivot, x='date', y='markup', labels={'markup': 'Markup (GH₵/kg)', 'date': ''})
            fig_markup.update_traces(line=dict(color='#111111', width=2))
            fig_markup.add_hline(y=0, line_dash="dot", line_color="#9A9A9A")
            fig_markup.update_layout(height=280, margin=dict(l=50, r=20, t=10, b=40), hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_markup, use_container_width=True, theme=None)
        else:
            st.info("No matched wholesale/retail pairs available for this commodity at Techiman.")
        st.markdown('</div>', unsafe_allow_html=True)

    # ------------------- ROW 3 (Full Width) -------------------
    # ------------------------------------------------------------------------------
    # TAB 5: Lydia Oduro — COMMODITY VOLATILITY & RISK MATRIX
    # ------------------------------------------------------------------------------
    st.markdown('<div class="chart-container"><div class="chart-title">Price Volatility & Market Risk Ranking</div>', unsafe_allow_html=True)

    # **PLACE YOUR CODE HERE** (Lydia Oduro)
    risk_df = df.dropna(subset=['price_per_kg'])
    volatility_summary = risk_df.groupby('commodity')['price_per_kg'].agg(mean_price='mean', std_price='std', n='count').reset_index()
    volatility_summary = volatility_summary[volatility_summary['n'] >= 12]
    volatility_summary['cv'] = volatility_summary['std_price'] / volatility_summary['mean_price']
    volatility_summary = volatility_summary.sort_values('cv', ascending=True).tail(10)

    fig_risk = px.bar(volatility_summary, x='cv', y='commodity', orientation='h', labels={'cv': 'Volatility Coefficient (Std Dev / Mean)', 'commodity': ''})
    fig_risk.update_traces(marker_color='#111111')
    fig_risk.update_layout(height=350, margin=dict(l=140, r=20, t=10, b=40), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis=dict(ticklabelstandoff=12))
    st.plotly_chart(fig_risk, use_container_width=True, theme=None)
    st.markdown('</div>', unsafe_allow_html=True)

else:
    st.warning("Awaiting valid dataset load. Please verify cloud credentials or local cache.")    