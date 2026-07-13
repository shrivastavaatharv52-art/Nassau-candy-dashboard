import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Nassau Candy – Profitability Dashboard",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #0f0f1a; color: #e0e0e0; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1a1a2e; border-right: 1px solid #2e2e4e; }

    /* Metric cards */
    [data-testid="stMetric"] {
        background-color: #1e1e3a;
        border: 1px solid #2e2e5e;
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="stMetricLabel"] { color: #a0a0c0 !important; font-size: 13px !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 26px !important; font-weight: 700 !important; }
    [data-testid="stMetricDelta"] { font-size: 13px !important; }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1a1a2e;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #a0a0c0;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #6c63ff !important;
        color: white !important;
    }

    /* Headers */
    h1 { color: #ffffff !important; }
    h2 { color: #c0c0e0 !important; }
    h3 { color: #a0a0cc !important; font-size: 16px !important; }

    /* Divider */
    hr { border-color: #2e2e4e; }

    /* Dataframe */
    [data-testid="stDataFrame"] { border-radius: 10px; }

    /* Section cards */
    .section-card {
        background-color: #1e1e3a;
        border: 1px solid #2e2e5e;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# DATA LOAD & PREP
# ─────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("Nassau_Candy_Distributor.csv")
    df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True)
    df['Ship Date']  = pd.to_datetime(df['Ship Date'],  dayfirst=True)
    df['Month']      = df['Order Date'].dt.to_period('M').astype(str)
    df['Quarter']    = df['Order Date'].dt.to_period('Q').astype(str)
    df['Gross Margin %'] = (df['Gross Profit'] / df['Sales'] * 100).round(2)
    df['Profit per Unit'] = (df['Gross Profit'] / df['Units']).round(2)
    # Factory mapping from brief
    factory_map = {
        'Wonka Bar - Nutty Crunch Surprise' : "Let's O'Nuts",
        'Wonka Bar - Fudge Mallows'         : "Let's O'Nuts",
        'Wonka Bar -Scrumdiddlyumptious'    : "Let's O'Nuts",
        'Wonka Bar - Milk Chocolate'        : "Wicked Choccy's",
        'Wonka Bar - Triple Dazzle Caramel' : "Wicked Choccy's",
        'Laffy Taffy'                       : 'Sugar Shock',
        'SweeTARTS'                         : 'Sugar Shock',
        'Nerds'                             : 'Sugar Shock',
        'Fun Dip'                           : 'Sugar Shock',
        'Fizzy Lifting Drinks'              : 'Sugar Shock',
        'Everlasting Gobstopper'            : 'Secret Factory',
        'Hair Toffee'                       : 'The Other Factory',
        'Lickable Wallpaper'                : 'Secret Factory',
        'Wonka Gum'                         : 'Secret Factory',
        'Kazookles'                         : 'The Other Factory',
    }
    df['Factory'] = df['Product Name'].map(factory_map)
    return df

df_raw = load_data()

# ─────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍬 Nassau Candy")
    st.markdown("**Profitability Analytics**")
    st.markdown("---")

    # Date range
    st.markdown("### 📅 Date Range")
    min_date = df_raw['Order Date'].min().date()
    max_date = df_raw['Order Date'].max().date()
    date_range = st.date_input("Select range", value=(min_date, max_date),
                               min_value=min_date, max_value=max_date)

    st.markdown("### 🏭 Division")
    divisions = ['All'] + sorted(df_raw['Division'].unique().tolist())
    selected_div = st.multiselect("Division", options=divisions[1:],
                                  default=divisions[1:])

    st.markdown("### 📊 Margin Threshold")
    margin_threshold = st.slider("Min Gross Margin %", 0, 100, 0, 5)

    st.markdown("### 🔍 Product Search")
    product_search = st.text_input("Search product name", "")

    st.markdown("---")
    st.caption("Data: Nassau Candy Distributor 2025")

# ─────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────
df = df_raw.copy()

if len(date_range) == 2:
    df = df[(df['Order Date'].dt.date >= date_range[0]) &
            (df['Order Date'].dt.date <= date_range[1])]

if selected_div:
    df = df[df['Division'].isin(selected_div)]

df = df[df['Gross Margin %'] >= margin_threshold]

if product_search:
    df = df[df['Product Name'].str.contains(product_search, case=False, na=False)]

# Guard: empty data
if df.empty:
    st.warning("No data matches your filters. Please adjust the sidebar.")
    st.stop()

# ─────────────────────────────────────────────
# AGGREGATIONS
# ─────────────────────────────────────────────
total_sales   = df['Sales'].sum()
total_profit  = df['Gross Profit'].sum()
total_cost    = df['Cost'].sum()
total_units   = df['Units'].sum()
overall_margin = total_profit / total_sales * 100

product_df = df.groupby(['Product Name','Division']).agg(
    Total_Sales   =('Sales','sum'),
    Total_Profit  =('Gross Profit','sum'),
    Total_Units   =('Units','sum'),
    Total_Cost    =('Cost','sum'),
    Order_Count   =('Order ID','nunique')
).reset_index()
product_df['Gross Margin %']       = (product_df['Total_Profit'] / product_df['Total_Sales'] * 100).round(2)
product_df['Profit per Unit']      = (product_df['Total_Profit'] / product_df['Total_Units']).round(2)
product_df['Revenue Contribution %'] = (product_df['Total_Sales']  / total_sales  * 100).round(2)
product_df['Profit Contribution %']  = (product_df['Total_Profit'] / total_profit * 100).round(2)

division_df = df.groupby('Division').agg(
    Total_Sales  =('Sales','sum'),
    Total_Profit =('Gross Profit','sum'),
    Total_Cost   =('Cost','sum'),
    Total_Units  =('Units','sum')
).reset_index()
division_df['Margin %'] = (division_df['Total_Profit'] / division_df['Total_Sales'] * 100).round(2)

monthly_df = df.groupby(['Month','Division']).agg(
    Sales  =('Sales','sum'),
    Profit =('Gross Profit','sum')
).reset_index()
monthly_df['Margin %'] = (monthly_df['Profit'] / monthly_df['Sales'] * 100).round(2)

# ─────────────────────────────────────────────
# PLOTLY THEME
# ─────────────────────────────────────────────
COLORS = ['#6c63ff','#ff6584','#43e97b','#f7971e','#00d2ff',
          '#a18cd1','#fda085','#f6d365','#fccb90','#d57eeb']
BGCOLOR  = '#0f0f1a'
PAPERBG  = '#1e1e3a'
FONT_CLR = '#c0c0e0'
GRID_CLR = '#2e2e4e'

def base_layout(title=""):
    return dict(
        title=dict(text=title, font=dict(color=FONT_CLR, size=15)),
        plot_bgcolor=BGCOLOR, paper_bgcolor=PAPERBG,
        font=dict(color=FONT_CLR, size=12),
        xaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR),
        yaxis=dict(gridcolor=GRID_CLR, zerolinecolor=GRID_CLR),
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color=FONT_CLR))
    )

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown("# 🍬 Nassau Candy Distributor")
st.markdown("### Product Line Profitability & Margin Performance Analysis")
st.markdown("---")

# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Total Revenue",    f"${total_sales:,.0f}")
k2.metric("📈 Gross Profit",     f"${total_profit:,.0f}")
k3.metric("🏭 Total Cost",       f"${total_cost:,.0f}")
k4.metric("📦 Units Sold",       f"{total_units:,}")
k5.metric("📊 Avg Gross Margin", f"{overall_margin:.1f}%")

st.markdown("---")

# ─────────────────────────────────────────────
# CRITICAL ALERTS
# ─────────────────────────────────────────────
critical = product_df[product_df['Gross Margin %'] < 20]
warning  = product_df[(product_df['Gross Margin %'] >= 20) & (product_df['Gross Margin %'] < 40)]

if not critical.empty:
    for _, row in critical.iterrows():
        st.markdown(
            f"<div style='background:#ff000015; border-left:5px solid #ff4444; "
            f"padding:12px 16px; border-radius:8px; margin-bottom:8px;'>"
            f"🚨 <b>CRITICAL:</b> <b>{row['Product Name']}</b> has a gross margin of only "
            f"<b>{row['Gross Margin %']:.1f}%</b> — consuming nearly all revenue in cost. "
            f"Immediate review required.</div>",
            unsafe_allow_html=True
        )

if not warning.empty:
    for _, row in warning.iterrows():
        st.markdown(
            f"<div style='background:#f7971e15; border-left:5px solid #f7971e; "
            f"padding:12px 16px; border-radius:8px; margin-bottom:8px;'>"
            f"⚠️ <b>WARNING:</b> <b>{row['Product Name']}</b> margin is <b>{row['Gross Margin %']:.1f}%</b> "
            f"— below acceptable threshold.</div>",
            unsafe_allow_html=True
        )

# ─────────────────────────────────────────────
# KEY INSIGHTS PANEL
# ─────────────────────────────────────────────
st.markdown("### 🔎 Key Insights")

insights = []

top_product = product_df.sort_values('Total_Profit', ascending=False).iloc[0]
insights.append(
    f"<b>🏆 Top Profit Driver:</b> <b>{top_product['Product Name']}</b> generates "
    f"<b>${top_product['Total_Profit']:,.0f}</b> in gross profit "
    f"({top_product['Profit Contribution %']:.1f}% of total) at a <b>{top_product['Gross Margin %']:.1f}%</b> margin."
)

choc = product_df[product_df['Division'] == 'Chocolate']['Total_Sales'].sum()
choc_share = choc / total_sales * 100 if total_sales > 0 else 0
if choc_share > 80:
    insights.append(
        f"<b>⚠️ Concentration Risk:</b> The Chocolate division accounts for "
        f"<b>{choc_share:.1f}%</b> of total revenue — heavy reliance on a single division."
    )

worst = product_df.sort_values('Gross Margin %').iloc[0]
insights.append(
    f"<b>📉 Lowest Margin Product:</b> <b>{worst['Product Name']}</b> has only "
    f"<b>{worst['Gross Margin %']:.1f}%</b> margin — generating ${worst['Total_Profit']:,.0f} profit "
    f"on ${worst['Total_Sales']:,.0f} revenue."
)

pareto_check = product_df.sort_values('Total_Profit', ascending=False).copy()
pareto_check['cum'] = pareto_check['Total_Profit'].cumsum() / pareto_check['Total_Profit'].sum() * 100
products_for_80 = int((pareto_check['cum'] < 80).sum()) + 1
insights.append(
    f"<b>📊 Pareto Finding:</b> Only <b>{products_for_80} products</b> out of "
    f"{len(product_df)} drive 80% of gross profit — a highly concentrated profit base."
)

best_margin = product_df.sort_values('Gross Margin %', ascending=False).iloc[0]
insights.append(
    f"<b>✅ Highest Margin:</b> <b>{best_margin['Product Name']}</b> leads with "
    f"<b>{best_margin['Gross Margin %']:.1f}%</b> gross margin — most efficient product in the portfolio."
)

for insight in insights:
    st.markdown(
        f"<div style='background:#1e1e3a; border:1px solid #2e2e5e; border-radius:10px; "
        f"padding:14px 18px; margin-bottom:10px; font-size:14px; color:#e0e0e0;'>"
        f"{insight}</div>",
        unsafe_allow_html=True
    )

st.markdown("---")

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🏆 Product Profitability",
    "🏭 Division Performance",
    "📊 Profit Concentration"
])

# ══════════════════════════════════════════════
# TAB 1 — PRODUCT PROFITABILITY
# ══════════════════════════════════════════════
with tab1:
    st.markdown("## Product Profitability Overview")

    # ── Leaderboard ──────────────────────────
    st.markdown("### 🥇 Gross Margin Leaderboard")
    sorted_prod = product_df.sort_values('Gross Margin %', ascending=False)

    fig_lb = go.Figure()
    bar_colors = ['#6c63ff' if m >= overall_margin else '#ff6584'
                  for m in sorted_prod['Gross Margin %']]
    fig_lb.add_trace(go.Bar(
        x=sorted_prod['Gross Margin %'],
        y=sorted_prod['Product Name'],
        orientation='h',
        marker_color=bar_colors,
        text=[f"{m:.1f}%" for m in sorted_prod['Gross Margin %']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Margin: %{x:.1f}%<extra></extra>'
    ))
    fig_lb.add_vline(x=overall_margin, line_dash="dash",
                     line_color="#f7971e", annotation_text=f"Avg {overall_margin:.1f}%",
                     annotation_font_color="#f7971e")
    fig_lb.update_layout(**base_layout("Gross Margin % by Product"),
                          height=480,
                          yaxis=dict(autorange='reversed', gridcolor=GRID_CLR))
    st.plotly_chart(fig_lb, use_container_width=True)

    # ── Profit & Revenue Contribution ────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💰 Profit Contribution %")
        fig_pc = px.pie(
            product_df.sort_values('Profit Contribution %', ascending=False),
            values='Profit Contribution %', names='Product Name',
            color_discrete_sequence=COLORS, hole=0.45
        )
        fig_pc.update_layout(paper_bgcolor=PAPERBG, plot_bgcolor=BGCOLOR,
                              font=dict(color=FONT_CLR), height=380,
                              margin=dict(l=20,r=20,t=30,b=20),
                              legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10)))
        fig_pc.update_traces(textposition='inside', textinfo='percent',
                              hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>')
        st.plotly_chart(fig_pc, use_container_width=True)

    with col2:
        st.markdown("### 📦 Revenue Contribution %")
        fig_rc = px.pie(
            product_df.sort_values('Revenue Contribution %', ascending=False),
            values='Revenue Contribution %', names='Product Name',
            color_discrete_sequence=COLORS[::-1], hole=0.45
        )
        fig_rc.update_layout(paper_bgcolor=PAPERBG, plot_bgcolor=BGCOLOR,
                              font=dict(color=FONT_CLR), height=380,
                              margin=dict(l=20,r=20,t=30,b=20),
                              legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10)))
        fig_rc.update_traces(textposition='inside', textinfo='percent',
                              hovertemplate='<b>%{label}</b><br>%{value:.1f}%<extra></extra>')
        st.plotly_chart(fig_rc, use_container_width=True)

    # ── Profit per Unit ──────────────────────
    st.markdown("### 🎯 Profit per Unit by Product")
    ppu = product_df.sort_values('Profit per Unit', ascending=False)
    fig_ppu = px.bar(
        ppu, x='Product Name', y='Profit per Unit',
        color='Division', color_discrete_sequence=COLORS,
        text='Profit per Unit'
    )
    fig_ppu.update_traces(texttemplate='$%{text:.2f}', textposition='outside')
    fig_ppu.update_layout(**base_layout("Profit per Unit"), height=380,
                           xaxis_tickangle=-35)
    st.plotly_chart(fig_ppu, use_container_width=True)

    # ── Product Data Table ───────────────────
    st.markdown("### 📋 Full Product Summary Table")
    display_cols = ['Product Name','Division','Total_Sales','Total_Profit',
                    'Total_Units','Gross Margin %','Profit per Unit',
                    'Revenue Contribution %','Profit Contribution %']
    styled = product_df[display_cols].sort_values('Gross Margin %', ascending=False).reset_index(drop=True)
    styled.columns = ['Product','Division','Revenue ($)','Profit ($)',
                      'Units','Margin %','Profit/Unit ($)','Rev Contrib %','Profit Contrib %']
    st.dataframe(
        styled.style
            .format({'Revenue ($)': '${:,.2f}', 'Profit ($)': '${:,.2f}',
                     'Profit/Unit ($)': '${:.2f}',
                     'Margin %': '{:.1f}%', 'Rev Contrib %': '{:.2f}%',
                     'Profit Contrib %': '{:.2f}%'})
            .background_gradient(subset=['Margin %'], cmap='RdYlGn'),
        use_container_width=True, hide_index=True
    )

# ══════════════════════════════════════════════
# TAB 2 — DIVISION PERFORMANCE
# ══════════════════════════════════════════════
with tab2:
    st.markdown("## Division Performance Dashboard")

    # ── Revenue vs Profit ────────────────────
    st.markdown("### 💹 Revenue vs Profit by Division")
    fig_rvp = go.Figure()
    fig_rvp.add_trace(go.Bar(
        name='Revenue', x=division_df['Division'],
        y=division_df['Total_Sales'], marker_color='#6c63ff',
        text=[f"${v:,.0f}" for v in division_df['Total_Sales']],
        textposition='outside'
    ))
    fig_rvp.add_trace(go.Bar(
        name='Gross Profit', x=division_df['Division'],
        y=division_df['Total_Profit'], marker_color='#43e97b',
        text=[f"${v:,.0f}" for v in division_df['Total_Profit']],
        textposition='outside'
    ))
    fig_rvp.add_trace(go.Bar(
        name='Cost', x=division_df['Division'],
        y=division_df['Total_Cost'], marker_color='#ff6584',
        text=[f"${v:,.0f}" for v in division_df['Total_Cost']],
        textposition='outside'
    ))
    fig_rvp.update_layout(**base_layout("Revenue, Profit & Cost by Division"),
                           barmode='group', height=400)
    st.plotly_chart(fig_rvp, use_container_width=True)

    col1, col2 = st.columns(2)

    # ── Margin by Division ───────────────────
    with col1:
        st.markdown("### 📊 Gross Margin % by Division")
        fig_mg = px.bar(
            division_df.sort_values('Margin %', ascending=False),
            x='Division', y='Margin %',
            color='Margin %', color_continuous_scale='RdYlGn',
            text='Margin %'
        )
        fig_mg.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_mg.add_hline(y=overall_margin, line_dash='dash',
                         line_color='#f7971e',
                         annotation_text=f"Overall {overall_margin:.1f}%",
                         annotation_font_color='#f7971e')
        fig_mg.update_layout(**base_layout(), height=360,
                              coloraxis_showscale=False)
        st.plotly_chart(fig_mg, use_container_width=True)

    # ── Revenue Split ────────────────────────
    with col2:
        st.markdown("### 🍩 Revenue Split by Division")
        fig_rsplit = px.pie(
            division_df, values='Total_Sales', names='Division',
            color_discrete_sequence=COLORS, hole=0.5
        )
        fig_rsplit.update_layout(paper_bgcolor=PAPERBG, plot_bgcolor=BGCOLOR,
                                  font=dict(color=FONT_CLR), height=360,
                                  margin=dict(l=20,r=20,t=30,b=20))
        fig_rsplit.update_traces(textposition='inside', textinfo='label+percent')
        st.plotly_chart(fig_rsplit, use_container_width=True)

    # ── Monthly Margin Trend ─────────────────
    st.markdown("### 📈 Monthly Margin Trend by Division")
    fig_trend = px.line(
        monthly_df, x='Month', y='Margin %', color='Division',
        color_discrete_sequence=COLORS, markers=True,
        line_shape='spline'
    )
    fig_trend.add_hline(y=overall_margin, line_dash='dot',
                        line_color='#f7971e',
                        annotation_text=f"Avg {overall_margin:.1f}%")
    fig_trend.update_layout(**base_layout("Gross Margin % Over Time"), height=380,
                             xaxis_tickangle=-45)
    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Cost vs Sales Scatter ────────────────
    st.markdown("### 🔍 Cost vs Sales Diagnostic (Product Level)")
    fig_scatter = px.scatter(
        product_df, x='Total_Sales', y='Total_Cost',
        size='Total_Units', color='Division',
        hover_name='Product Name',
        color_discrete_sequence=COLORS,
        text='Product Name',
        size_max=60
    )
    # Add diagonal = 50% margin reference
    max_val = max(product_df['Total_Sales'].max(), product_df['Total_Cost'].max())
    fig_scatter.add_trace(go.Scatter(
        x=[0, max_val], y=[0, max_val * 0.5],
        mode='lines', name='50% Margin Line',
        line=dict(color='#f7971e', dash='dash')
    ))
    fig_scatter.update_traces(textposition='top center', textfont_size=9)
    fig_scatter.update_layout(**base_layout("Cost vs Sales — bubble size = units sold"),
                               height=450)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # ── Margin Risk Flags ────────────────────
    st.markdown("### 🚨 Margin Risk Flags")
    low_margin = product_df[product_df['Gross Margin %'] < 50].sort_values('Gross Margin %')
    if not low_margin.empty:
        for _, row in low_margin.iterrows():
            color = "#ff4444" if row['Gross Margin %'] < 30 else "#f7971e"
            st.markdown(
                f"<div style='background:{color}22; border-left: 4px solid {color}; "
                f"padding:10px; border-radius:6px; margin-bottom:8px;'>"
                f"⚠️ <b>{row['Product Name']}</b> ({row['Division']}) — "
                f"Margin: <b>{row['Gross Margin %']:.1f}%</b> | "
                f"Profit: ${row['Total_Profit']:,.2f}</div>",
                unsafe_allow_html=True
            )
    else:
        st.success("✅ All products exceed the margin threshold set in filters.")

# ══════════════════════════════════════════════
# TAB 3 — PROFIT CONCENTRATION (PARETO)
# ══════════════════════════════════════════════
with tab3:
    st.markdown("## Profit Concentration Analysis")

    # ── Pareto — Revenue ─────────────────────
    st.markdown("### 📦 Revenue Pareto — Which products drive 80% of revenue?")
    pareto_rev = product_df.sort_values('Total_Sales', ascending=False).copy()
    pareto_rev['Cumulative Revenue %'] = (
        pareto_rev['Total_Sales'].cumsum() / pareto_rev['Total_Sales'].sum() * 100
    )

    fig_par_rev = make_subplots(specs=[[{"secondary_y": True}]])
    fig_par_rev.add_trace(go.Bar(
        x=pareto_rev['Product Name'], y=pareto_rev['Total_Sales'],
        name='Revenue', marker_color='#6c63ff',
        text=[f"${v:,.0f}" for v in pareto_rev['Total_Sales']],
        textposition='outside'
    ), secondary_y=False)
    fig_par_rev.add_trace(go.Scatter(
        x=pareto_rev['Product Name'], y=pareto_rev['Cumulative Revenue %'],
        name='Cumulative %', mode='lines+markers',
        line=dict(color='#f7971e', width=2), marker=dict(size=7)
    ), secondary_y=True)
    fig_par_rev.add_hline(y=80, line_dash='dash', line_color='#ff6584',
                           annotation_text='80% Line', secondary_y=True)
    fig_par_rev.update_layout(
        paper_bgcolor=PAPERBG, plot_bgcolor=BGCOLOR,
        font=dict(color=FONT_CLR), height=430,
        margin=dict(l=40,r=40,t=50,b=80),
        xaxis=dict(tickangle=-35, gridcolor=GRID_CLR),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        title=dict(text='Revenue Pareto Analysis', font=dict(color=FONT_CLR))
    )
    fig_par_rev.update_yaxes(title_text="Revenue ($)", gridcolor=GRID_CLR, secondary_y=False)
    fig_par_rev.update_yaxes(title_text="Cumulative %", secondary_y=True,
                              range=[0,105], gridcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_par_rev, use_container_width=True)

    # ── Pareto — Profit ──────────────────────
    st.markdown("### 💰 Profit Pareto — Which products drive 80% of profit?")
    pareto_pft = product_df.sort_values('Total_Profit', ascending=False).copy()
    pareto_pft['Cumulative Profit %'] = (
        pareto_pft['Total_Profit'].cumsum() / pareto_pft['Total_Profit'].sum() * 100
    )

    fig_par_pft = make_subplots(specs=[[{"secondary_y": True}]])
    fig_par_pft.add_trace(go.Bar(
        x=pareto_pft['Product Name'], y=pareto_pft['Total_Profit'],
        name='Profit', marker_color='#43e97b',
        text=[f"${v:,.0f}" for v in pareto_pft['Total_Profit']],
        textposition='outside'
    ), secondary_y=False)
    fig_par_pft.add_trace(go.Scatter(
        x=pareto_pft['Product Name'], y=pareto_pft['Cumulative Profit %'],
        name='Cumulative %', mode='lines+markers',
        line=dict(color='#f7971e', width=2), marker=dict(size=7)
    ), secondary_y=True)
    fig_par_pft.add_hline(y=80, line_dash='dash', line_color='#ff6584',
                           annotation_text='80% Line', secondary_y=True)
    fig_par_pft.update_layout(
        paper_bgcolor=PAPERBG, plot_bgcolor=BGCOLOR,
        font=dict(color=FONT_CLR), height=430,
        margin=dict(l=40,r=40,t=50,b=80),
        xaxis=dict(tickangle=-35, gridcolor=GRID_CLR),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        title=dict(text='Profit Pareto Analysis', font=dict(color=FONT_CLR))
    )
    fig_par_pft.update_yaxes(title_text="Profit ($)", gridcolor=GRID_CLR, secondary_y=False)
    fig_par_pft.update_yaxes(title_text="Cumulative %", secondary_y=True,
                              range=[0,105], gridcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_par_pft, use_container_width=True)

    # ── Dependency Indicators ────────────────
    st.markdown("### 🔗 Dependency Indicators")
    top3_rev_share = pareto_rev.head(3)['Revenue Contribution %'].sum()
    top3_pft_share = pareto_pft.head(3)['Profit Contribution %'].sum()
    top1_product   = pareto_pft.iloc[0]['Product Name']
    top1_pft_share = pareto_pft.iloc[0]['Profit Contribution %']

    d1, d2, d3 = st.columns(3)
    d1.metric("Top 3 Products — Revenue Share", f"{top3_rev_share:.1f}%",
              delta="Concentration risk" if top3_rev_share > 70 else "Healthy spread",
              delta_color="inverse" if top3_rev_share > 70 else "normal")
    d2.metric("Top 3 Products — Profit Share", f"{top3_pft_share:.1f}%",
              delta="Concentration risk" if top3_pft_share > 70 else "Healthy spread",
              delta_color="inverse" if top3_pft_share > 70 else "normal")
    d3.metric(f"#{1} Profit Driver", top1_product[:20],
              delta=f"{top1_pft_share:.1f}% of all profit")

    # ── Margin Volatility ────────────────────
    st.markdown("### 📉 Margin Volatility by Product")
    monthly_prod = df.groupby(['Month','Product Name']).agg(
        Sales  =('Sales','sum'),
        Profit =('Gross Profit','sum')
    ).reset_index()
    monthly_prod['Margin %'] = (monthly_prod['Profit'] / monthly_prod['Sales'] * 100).round(2)
    volatility = monthly_prod.groupby('Product Name')['Margin %'].std().reset_index()
    volatility.columns = ['Product Name','Margin Volatility (Std Dev)']
    volatility = volatility.sort_values('Margin Volatility (Std Dev)', ascending=False)

    fig_vol = px.bar(
        volatility, x='Product Name', y='Margin Volatility (Std Dev)',
        color='Margin Volatility (Std Dev)',
        color_continuous_scale='RdYlGn_r',
        text='Margin Volatility (Std Dev)'
    )
    fig_vol.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig_vol.update_layout(**base_layout("Margin Volatility — Higher = Less Predictable"),
                           height=370, xaxis_tickangle=-35,
                           coloraxis_showscale=False)
    st.plotly_chart(fig_vol, use_container_width=True)

    # ── Product Matrix ───────────────────────
    st.markdown("### 🎯 Product Quadrant Matrix (Sales vs Margin)")
    fig_matrix = px.scatter(
        product_df,
        x='Revenue Contribution %', y='Gross Margin %',
        size='Total_Profit', color='Division',
        hover_name='Product Name',
        color_discrete_sequence=COLORS,
        text='Product Name',
        size_max=60
    )
    avg_rev = product_df['Revenue Contribution %'].mean()
    avg_mar = product_df['Gross Margin %'].mean()
    fig_matrix.add_hline(y=avg_mar, line_dash='dash', line_color='rgba(255,255,255,0.25)')
    fig_matrix.add_vline(x=avg_rev, line_dash='dash', line_color='rgba(255,255,255,0.25)')
    # Quadrant labels
    fig_matrix.add_annotation(x=avg_rev*0.4, y=avg_mar*1.3, text="Low Rev / High Margin",
                               showarrow=False, font=dict(color='#43e97b', size=10))
    fig_matrix.add_annotation(x=avg_rev*2.5, y=avg_mar*1.3, text="⭐ Stars",
                               showarrow=False, font=dict(color='#43e97b', size=11))
    fig_matrix.add_annotation(x=avg_rev*0.4, y=avg_mar*0.5, text="Watch / Cut",
                               showarrow=False, font=dict(color='#ff6584', size=10))
    fig_matrix.add_annotation(x=avg_rev*2.5, y=avg_mar*0.5, text="High Rev / Low Margin",
                               showarrow=False, font=dict(color='#f7971e', size=10))
    fig_matrix.update_traces(textposition='top center', textfont_size=9)
    fig_matrix.update_layout(**base_layout("Product Quadrant: Revenue Contribution vs Gross Margin %"),
                              height=480)
    st.plotly_chart(fig_matrix, use_container_width=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.caption("Nassau Candy Distributor | Product Line Profitability & Margin Performance Analysis | 2025 Data")
