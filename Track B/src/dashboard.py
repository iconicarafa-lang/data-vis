import time
import requests
import datetime
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Westeros Real-Time Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INITIALIZE SESSION STATE ---
if 'history' not in st.session_state:
    st.session_state.history = []
if 'live_active' not in st.session_state:
    st.session_state.live_active = True

# Paper Trading State (Starting Cash: $100M USD)
if 'cash' not in st.session_state:
    st.session_state.cash = 100000000.0
if 'btc_held' not in st.session_state:
    st.session_state.btc_held = 0.0
if 'btc_cost_basis' not in st.session_state:
    st.session_state.btc_cost_basis = 0.0
if 'eth_held' not in st.session_state:
    st.session_state.eth_held = 0.0
if 'eth_cost_basis' not in st.session_state:
    st.session_state.eth_cost_basis = 0.0
if 'sol_held' not in st.session_state:
    st.session_state.sol_held = 0.0
if 'sol_cost_basis' not in st.session_state:
    st.session_state.sol_cost_basis = 0.0
if 'ada_held' not in st.session_state:
    st.session_state.ada_held = 0.0
if 'ada_cost_basis' not in st.session_state:
    st.session_state.ada_cost_basis = 0.0

# Asset Last Prices (Fallback/Initial Values)
if 'last_btc_price' not in st.session_state:
    st.session_state.last_btc_price = 95000.0
if 'last_eth_price' not in st.session_state:
    st.session_state.last_eth_price = 3000.0
if 'last_sol_price' not in st.session_state:
    st.session_state.last_sol_price = 180.0
if 'last_ada_price' not in st.session_state:
    st.session_state.last_ada_price = 0.50

# System State
if 'trade_alert' not in st.session_state:
    st.session_state.trade_alert = None
if 'last_trade_status' not in st.session_state:
    st.session_state.last_trade_status = None
if 'realized_pnl' not in st.session_state:
    st.session_state.realized_pnl = 0.0
if 'trades_log' not in st.session_state:
    st.session_state.trades_log = []

# --- INJECT PREMIUM CSS (SaaS Grid Styling) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background-color: #07090e;
        color: #f8f8f2;
        font-family: 'Inter', sans-serif;
    }
    
    /* Auto-fit responsive grid layout */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 20px;
        margin-bottom: 25px;
        width: 100%;
    }
    
    .kpi-card {
        background: linear-gradient(135deg, rgba(22, 25, 37, 0.7) 0%, rgba(15, 17, 26, 0.7) 100%);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 24px;
        height: 155px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
    }
    
    .kpi-card:hover {
        border-color: rgba(189, 147, 249, 0.3);
        transform: translateY(-2px);
    }
    
    .kpi-card-alert {
        background: linear-gradient(135deg, rgba(230, 57, 70, 0.15) 0%, rgba(230, 57, 70, 0.05) 100%) !important;
        border: 1px solid #ff5555 !important;
        box-shadow: 0 0 25px rgba(255, 85, 85, 0.25) !important;
        animation: pulse 1.5s infinite alternate;
    }
    
    .kpi-label {
        font-family: 'Outfit', sans-serif;
        font-size: 11px;
        text-transform: uppercase;
        color: #9aa0a6;
        font-weight: 600;
        letter-spacing: 1px;
    }
    
    .kpi-val {
        font-family: 'Outfit', sans-serif;
        font-size: 2.1rem;
        font-weight: 800;
        line-height: 1.1;
        margin: 6px 0;
    }
    
    .kpi-change-up {
        font-size: 13px;
        color: #50fa7b;
        font-weight: 600;
    }

    .kpi-change-down {
        font-size: 13px;
        color: #ff5555;
        font-weight: 600;
    }
    
    .alert-banner {
        padding: 16px 24px;
        border-radius: 12px;
        background: linear-gradient(135deg, #e63946 0%, #bd1f36 100%);
        border: 1px solid #ff5555;
        box-shadow: 0 0 25px rgba(255, 85, 85, 0.35);
        color: white;
        margin-bottom: 24px;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 14px;
    }

    .performance-card {
        background: rgba(22, 25, 37, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 20px;
        margin-top: 15px;
    }
    
    @keyframes pulse {
        0% { border-color: rgba(255, 85, 85, 0.4); box-shadow: 0 0 15px rgba(255, 85, 85, 0.15); }
        100% { border-color: rgba(255, 85, 85, 1); box-shadow: 0 0 30px rgba(255, 85, 85, 0.4); }
    }
</style>
""", unsafe_allow_html=True)

# --- CONSTANTS & API DETAILS ---
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,cardano&vs_currencies=usd&include_24hr_change=true"
WINDOW_MINUTES = 15

# --- SEED DATA FUNCTION ---
def seed_history(current_btc, current_eth, current_sol, current_ada):
    now = datetime.datetime.now()
    history = []
    for i in range(90, 0, -1):
        timestamp = now - datetime.timedelta(seconds=i * 10)
        import math
        btc_noise = (math.sin(i * 0.12) * 140) + (math.cos(i * 0.04) * 90)
        eth_noise = (math.sin(i * 0.12) * 6) + (math.cos(i * 0.04) * 3)
        sol_noise = (math.sin(i * 0.12) * 0.4) + (math.cos(i * 0.04) * 0.2)
        ada_noise = (math.sin(i * 0.12) * 0.01) + (math.cos(i * 0.04) * 0.005)
        history.append({
            "Time": timestamp,
            "Timestamp": timestamp.strftime("%H:%M:%S"),
            "Bitcoin": current_btc + btc_noise,
            "Ethereum": current_eth + eth_noise,
            "Solana": current_sol + sol_noise,
            "Cardano": current_ada + ada_noise
        })
    return history

# --- API INGESTION ---
def fetch_prices():
    try:
        t0 = time.time()
        response = requests.get(COINGECKO_API, timeout=5)
        latency_ms = int((time.time() - t0) * 1000)
        if response.status_code == 200:
            data = response.json()
            return {
                "btc_price": data['bitcoin']['usd'],
                "btc_change": data['bitcoin']['usd_24h_change'],
                "eth_price": data['ethereum']['usd'],
                "eth_change": data['ethereum']['usd_24h_change'],
                "sol_price": data['solana']['usd'],
                "sol_change": data['solana']['usd_24h_change'],
                "ada_price": data['cardano']['usd'],
                "ada_change": data['cardano']['usd_24h_change'],
                "success": True,
                "latency_ms": latency_ms
            }
        else:
            return {"success": False, "status_code": response.status_code, "latency_ms": latency_ms}
    except Exception as e:
        return {"success": False, "error": str(e), "latency_ms": 0}

# --- SIDEBAR CONTROL PANEL ---
st.sidebar.markdown("""
<div style="text-align: center; padding-bottom: 15px;">
    <h2 style="font-family: 'Outfit', sans-serif; font-weight: 800; letter-spacing: 1px; color: #bd93f9; text-transform: uppercase;">Westeros Engine</h2>
    <span style="font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #9aa0a6;">Live Control Panel</span>
</div>
""", unsafe_allow_html=True)

# 1. Simulator Core Info
st.sidebar.subheader("💼 Paper Trading Simulator")
st.sidebar.markdown(f"""
* **Available Cash**: `${st.session_state.cash:,.2f} USD`
* **BTC held**: `{st.session_state.btc_held:.4f} BTC`
* **ETH held**: `{st.session_state.eth_held:.4f} ETH`
* **SOL held**: `{st.session_state.sol_held:.4f} SOL`
* **ADA held**: `{st.session_state.ada_held:.4f} ADA`
""")

# Quick Add Funds button
if st.sidebar.button("💵 Add $10,000,000 Cash", use_container_width=True):
    st.session_state.cash += 10000000.0
    time_str = datetime.datetime.now().strftime("%H:%M:%S")
    msg = "Added $10,000,000.00 USD Cash to balance!"
    st.session_state.trade_alert = ("success", msg)
    st.session_state.last_trade_status = {"type": "success", "message": msg, "timestamp": time_str}
    st.toast("Added $10M Cash!", icon="💵")
    st.rerun()

trade_asset = st.sidebar.selectbox("Select Asset to Trade", ["Bitcoin", "Ethereum", "Solana", "Cardano"])
trade_action = st.sidebar.radio("Trade Action", ["Buy", "Sell"])
trade_amount = st.sidebar.number_input("Amount (units)", min_value=0.0001, max_value=1000000.0, value=1.0, step=1.0, format="%.4f")

if st.sidebar.button("⚡ Execute Trade", use_container_width=True):
    current_btc = st.session_state.last_btc_price
    current_eth = st.session_state.last_eth_price
    current_sol = st.session_state.last_sol_price
    current_ada = st.session_state.last_ada_price
    time_str = datetime.datetime.now().strftime("%H:%M:%S")
    
    if trade_asset == "Bitcoin":
        price = current_btc
        if trade_action == "Buy":
            cost = price * trade_amount
            if cost <= st.session_state.cash:
                st.session_state.cash -= cost
                st.session_state.btc_held += trade_amount
                st.session_state.btc_cost_basis += cost
                
                alert_text = f"SUCCESS: Bought {trade_amount:.4f} BTC at ${price:,.2f} (Total: ${cost:,.2f})"
                st.session_state.trade_alert = ("success", alert_text)
                st.session_state.last_trade_status = {"type": "success", "message": alert_text, "timestamp": time_str}
                st.session_state.trades_log.append(f"[{time_str}] 🟢 {alert_text}")
                st.toast("Trade executed successfully!", icon="✅")
                st.rerun()
            else:
                alert_text = "FAILED: Insufficient Cash Balance!"
                st.session_state.trade_alert = ("error", alert_text)
                st.session_state.last_trade_status = {"type": "error", "message": alert_text, "timestamp": time_str}
                st.toast("Trade failed: Insufficient Cash!", icon="❌")
                st.rerun()
        else: # Sell
            if st.session_state.btc_held >= trade_amount:
                pct_sold = trade_amount / st.session_state.btc_held
                realized_cost = st.session_state.btc_cost_basis * pct_sold
                st.session_state.btc_cost_basis -= realized_cost
                
                revenue = price * trade_amount
                trade_pnl = revenue - realized_cost
                st.session_state.cash += revenue
                st.session_state.btc_held -= trade_amount
                st.session_state.realized_pnl += trade_pnl
                
                alert_text = f"SUCCESS: Sold {trade_amount:.4f} BTC at ${price:,.2f} (Net P&L: {trade_pnl:+,.2f} USD)"
                st.session_state.trade_alert = ("success", alert_text)
                st.session_state.last_trade_status = {"type": "success", "message": alert_text, "timestamp": time_str}
                st.session_state.trades_log.append(f"[{time_str}] 🔴 {alert_text}")
                st.toast(f"Sold successfully! P&L: {trade_pnl:+,.2f}", icon="💰")
                st.rerun()
            else:
                alert_text = "FAILED: Insufficient BTC holdings to sell!"
                st.session_state.trade_alert = ("error", alert_text)
                st.session_state.last_trade_status = {"type": "error", "message": alert_text, "timestamp": time_str}
                st.toast("Trade failed: Insufficient holdings!", icon="❌")
                st.rerun()
                
    elif trade_asset == "Ethereum":
        price = current_eth
        if trade_action == "Buy":
            cost = price * trade_amount
            if cost <= st.session_state.cash:
                st.session_state.cash -= cost
                st.session_state.eth_held += trade_amount
                st.session_state.eth_cost_basis += cost
                
                alert_text = f"SUCCESS: Bought {trade_amount:.4f} ETH at ${price:,.2f} (Total: ${cost:,.2f})"
                st.session_state.trade_alert = ("success", alert_text)
                st.session_state.last_trade_status = {"type": "success", "message": alert_text, "timestamp": time_str}
                st.session_state.trades_log.append(f"[{time_str}] 🟢 {alert_text}")
                st.toast("Trade executed successfully!", icon="✅")
                st.rerun()
            else:
                alert_text = "FAILED: Insufficient Cash Balance!"
                st.session_state.trade_alert = ("error", alert_text)
                st.session_state.last_trade_status = {"type": "error", "message": alert_text, "timestamp": time_str}
                st.toast("Trade failed: Insufficient Cash!", icon="❌")
                st.rerun()
        else: # Sell
            if st.session_state.eth_held >= trade_amount:
                pct_sold = trade_amount / st.session_state.eth_held
                realized_cost = st.session_state.eth_cost_basis * pct_sold
                st.session_state.eth_cost_basis -= realized_cost
                
                revenue = price * trade_amount
                trade_pnl = revenue - realized_cost
                st.session_state.cash += revenue
                st.session_state.eth_held -= trade_amount
                st.session_state.realized_pnl += trade_pnl
                
                alert_text = f"SUCCESS: Sold {trade_amount:.4f} ETH at ${price:,.2f} (Net P&L: {trade_pnl:+,.2f} USD)"
                st.session_state.trade_alert = ("success", alert_text)
                st.session_state.last_trade_status = {"type": "success", "message": alert_text, "timestamp": time_str}
                st.session_state.trades_log.append(f"[{time_str}] 🔴 {alert_text}")
                st.toast(f"Sold successfully! P&L: {trade_pnl:+,.2f}", icon="💰")
                st.rerun()
            else:
                alert_text = "FAILED: Insufficient ETH holdings to sell!"
                st.session_state.trade_alert = ("error", alert_text)
                st.session_state.last_trade_status = {"type": "error", "message": alert_text, "timestamp": time_str}
                st.toast("Trade failed: Insufficient holdings!", icon="❌")
                st.rerun()

    elif trade_asset == "Solana":
        price = current_sol
        if trade_action == "Buy":
            cost = price * trade_amount
            if cost <= st.session_state.cash:
                st.session_state.cash -= cost
                st.session_state.sol_held += trade_amount
                st.session_state.sol_cost_basis += cost
                
                alert_text = f"SUCCESS: Bought {trade_amount:.4f} SOL at ${price:,.2f} (Total: ${cost:,.2f})"
                st.session_state.trade_alert = ("success", alert_text)
                st.session_state.last_trade_status = {"type": "success", "message": alert_text, "timestamp": time_str}
                st.session_state.trades_log.append(f"[{time_str}] 🟢 {alert_text}")
                st.toast("Trade executed successfully!", icon="✅")
                st.rerun()
            else:
                alert_text = "FAILED: Insufficient Cash Balance!"
                st.session_state.trade_alert = ("error", alert_text)
                st.session_state.last_trade_status = {"type": "error", "message": alert_text, "timestamp": time_str}
                st.toast("Trade failed: Insufficient Cash!", icon="❌")
                st.rerun()
        else: # Sell
            if st.session_state.sol_held >= trade_amount:
                pct_sold = trade_amount / st.session_state.sol_held
                realized_cost = st.session_state.sol_cost_basis * pct_sold
                st.session_state.sol_cost_basis -= realized_cost
                
                revenue = price * trade_amount
                trade_pnl = revenue - realized_cost
                st.session_state.cash += revenue
                st.session_state.sol_held -= trade_amount
                st.session_state.realized_pnl += trade_pnl
                
                alert_text = f"SUCCESS: Sold {trade_amount:.4f} SOL at ${price:,.2f} (Net P&L: {trade_pnl:+,.2f} USD)"
                st.session_state.trade_alert = ("success", alert_text)
                st.session_state.last_trade_status = {"type": "success", "message": alert_text, "timestamp": time_str}
                st.session_state.trades_log.append(f"[{time_str}] 🔴 {alert_text}")
                st.toast(f"Sold successfully! P&L: {trade_pnl:+,.2f}", icon="💰")
                st.rerun()
            else:
                alert_text = "FAILED: Insufficient SOL holdings to sell!"
                st.session_state.trade_alert = ("error", alert_text)
                st.session_state.last_trade_status = {"type": "error", "message": alert_text, "timestamp": time_str}
                st.toast("Trade failed: Insufficient holdings!", icon="❌")
                st.rerun()

    elif trade_asset == "Cardano":
        price = current_ada
        if trade_action == "Buy":
            cost = price * trade_amount
            if cost <= st.session_state.cash:
                st.session_state.cash -= cost
                st.session_state.ada_held += trade_amount
                st.session_state.ada_cost_basis += cost
                
                alert_text = f"SUCCESS: Bought {trade_amount:.4f} ADA at ${price:,.4f} (Total: ${cost:,.2f})"
                st.session_state.trade_alert = ("success", alert_text)
                st.session_state.last_trade_status = {"type": "success", "message": alert_text, "timestamp": time_str}
                st.session_state.trades_log.append(f"[{time_str}] 🟢 {alert_text}")
                st.toast("Trade executed successfully!", icon="✅")
                st.rerun()
            else:
                alert_text = "FAILED: Insufficient Cash Balance!"
                st.session_state.trade_alert = ("error", alert_text)
                st.session_state.last_trade_status = {"type": "error", "message": alert_text, "timestamp": time_str}
                st.toast("Trade failed: Insufficient Cash!", icon="❌")
                st.rerun()
        else: # Sell
            if st.session_state.ada_held >= trade_amount:
                pct_sold = trade_amount / st.session_state.ada_held
                realized_cost = st.session_state.ada_cost_basis * pct_sold
                st.session_state.ada_cost_basis -= realized_cost
                
                revenue = price * trade_amount
                trade_pnl = revenue - realized_cost
                st.session_state.cash += revenue
                st.session_state.ada_held -= trade_amount
                st.session_state.realized_pnl += trade_pnl
                
                alert_text = f"SUCCESS: Sold {trade_amount:.4f} ADA at ${price:,.4f} (Net P&L: {trade_pnl:+,.2f} USD)"
                st.session_state.trade_alert = ("success", alert_text)
                st.session_state.last_trade_status = {"type": "success", "message": alert_text, "timestamp": time_str}
                st.session_state.trades_log.append(f"[{time_str}] 🔴 {alert_text}")
                st.toast(f"Sold successfully! P&L: {trade_pnl:+,.2f}", icon="💰")
                st.rerun()
            else:
                alert_text = "FAILED: Insufficient ADA holdings to sell!"
                st.session_state.trade_alert = ("error", alert_text)
                st.session_state.last_trade_status = {"type": "error", "message": alert_text, "timestamp": time_str}
                st.toast("Trade failed: Insufficient holdings!", icon="❌")
                st.rerun()

st.sidebar.markdown("---")

# Expandable Settings to simplify the sidebar
with st.sidebar.expander("⚙️ Advanced Configuration", expanded=False):
    st.subheader("📡 Live Feed Controls")
    live_toggle = st.checkbox("Live Polling Active", value=st.session_state.live_active)
    st.session_state.live_active = live_toggle
    
    refresh_rate = st.slider("Polling Frequency (seconds)", min_value=5, max_value=30, value=10, step=1)
    
    st.markdown("---")
    st.subheader("🚨 Price Alert Thresholds")
    btc_alert_active = st.checkbox("Enable Bitcoin Alert", value=True)
    btc_high_threshold = st.number_input("BTC Upper Target Limit ($)", min_value=1000, value=95000, step=500)
    
    eth_alert_active = st.checkbox("Enable Ethereum Alert", value=True)
    eth_high_threshold = st.number_input("ETH Upper Target Limit ($)", min_value=100, value=3000, step=50)
    
    sol_alert_active = st.checkbox("Enable Solana Alert", value=True)
    sol_high_threshold = st.number_input("SOL Upper Target Limit ($)", min_value=1, value=200, step=5)
    
    ada_alert_active = st.checkbox("Enable Cardano Alert", value=True)
    ada_high_threshold = st.number_input("ADA Upper Target Limit ($)", min_value=0.01, value=1.0, step=0.05, format="%.2f")
    
    st.markdown("---")
    st.subheader("🧹 System Reset Options")
    col_reset1, col_reset2 = st.columns(2)
    with col_reset1:
        if st.button("Clear Chart", use_container_width=True):
            st.session_state.history = []
            st.toast("Chart history cleared!", icon="🧹")
            st.rerun()
    with col_reset2:
        if st.button("Reset Simulation", use_container_width=True):
            st.session_state.cash = 100000000.0
            st.session_state.btc_held = 0.0
            st.session_state.btc_cost_basis = 0.0
            st.session_state.eth_held = 0.0
            st.session_state.eth_cost_basis = 0.0
            st.session_state.sol_held = 0.0
            st.session_state.sol_cost_basis = 0.0
            st.session_state.ada_held = 0.0
            st.session_state.ada_cost_basis = 0.0
            st.session_state.realized_pnl = 0.0
            st.session_state.last_trade_status = None
            st.session_state.trade_alert = "🔄 Balance reset to $100,000,000.00 USD and holdings cleared."
            st.session_state.trades_log = []
            st.toast("Simulation reset!", icon="🔄")
            st.rerun()

# --- MAIN DASHBOARD CONTAINER ---
st.markdown("""
<div style="margin-bottom: 24px;">
    <h1 style="font-family: 'Outfit', sans-serif; font-weight: 800; font-size: 2.2rem; margin-bottom: 6px;">Live Cryptocurrency Terminal</h1>
    <p style="color: #9aa0a6; font-size: 13px;">SaaS-Grade Real-Time Dashboard • Ingesting CoinGecko Simple API</p>
</div>
""", unsafe_allow_html=True)

# 5. Display Trade Transaction Status Alert on Screen (Visible Banner)
if st.session_state.last_trade_status:
    l_type = st.session_state.last_trade_status["type"]
    l_msg = st.session_state.last_trade_status["message"]
    l_time = st.session_state.last_trade_status["timestamp"]
    
    if l_type == "success":
        st.markdown(f"""
        <div style="background: rgba(80, 250, 123, 0.08); border-left: 5px solid #50fa7b; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;">
            <span style="color: #9aa0a6; font-size: 10px; font-family: monospace; letter-spacing: 0.5px;">LAST ACTION FEEDBACK ({l_time})</span>
            <div style="color: #50fa7b; font-weight: 600; font-size: 14px; margin-top: 4px;">✅ {l_msg}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: rgba(255, 85, 85, 0.08); border-left: 5px solid #ff5555; padding: 12px 20px; border-radius: 8px; margin-bottom: 20px;">
            <span style="color: #9aa0a6; font-size: 10px; font-family: monospace; letter-spacing: 0.5px;">LAST ACTION FEEDBACK ({l_time})</span>
            <div style="color: #ff5555; font-weight: 600; font-size: 14px; margin-top: 4px;">❌ {l_msg}</div>
        </div>
        """, unsafe_allow_html=True)

# --- AUTO-REFRESH LIVE FRAGMENT (Modern Streamlit architecture) ---
@st.fragment(run_every=refresh_rate)
def render_live_view():
    now_time = datetime.datetime.now()
    rate_limit_active = False
    
    # Ingest data
    if st.session_state.live_active:
        data = fetch_prices()
        latency_ms = data.get("latency_ms", 0)
        if data["success"]:
            btc_p = data["btc_price"]
            btc_c = data["btc_change"]
            eth_p = data["eth_price"]
            eth_c = data["eth_change"]
            sol_p = data["sol_price"]
            sol_c = data["sol_change"]
            ada_p = data["ada_price"]
            ada_c = data["ada_change"]
            
            st.session_state.last_btc_price = btc_p
            st.session_state.last_eth_price = eth_p
            st.session_state.last_sol_price = sol_p
            st.session_state.last_ada_price = ada_p
            connection_status = "🟢 Connected & Live"
        else:
            btc_p = st.session_state.last_btc_price
            btc_c = 0.0
            eth_p = st.session_state.last_eth_price
            eth_c = 0.0
            sol_p = st.session_state.last_sol_price
            sol_c = 0.0
            ada_p = st.session_state.last_ada_price
            ada_c = 0.0
            rate_limit_active = True
            connection_status = "⚠️ Rate Limited (Cached)"
    else:
        btc_p = st.session_state.last_btc_price
        btc_c = 0.0
        eth_p = st.session_state.last_eth_price
        eth_c = 0.0
        sol_p = st.session_state.last_sol_price
        sol_c = 0.0
        ada_p = st.session_state.last_ada_price
        ada_c = 0.0
        latency_ms = 0
        connection_status = "⏸️ Polling Paused"
        
    # Seed history if empty
    if len(st.session_state.history) == 0:
        st.session_state.history = seed_history(btc_p, eth_p, sol_p, ada_p)
        
    # Log current tick if active
    if st.session_state.live_active and not rate_limit_active:
        st.session_state.history.append({
            "Time": now_time,
            "Timestamp": now_time.strftime("%H:%M:%S"),
            "Bitcoin": btc_p,
            "Ethereum": eth_p,
            "Solana": sol_p,
            "Cardano": ada_p
        })
        
    # Enforce sliding window (15 minutes)
    max_points = int((WINDOW_MINUTES * 60) / refresh_rate)
    if len(st.session_state.history) > max_points:
        st.session_state.history = st.session_state.history[-max_points:]
        
    # Calculate portfolio values dynamically
    portfolio_value = st.session_state.cash + (st.session_state.btc_held * btc_p) + (st.session_state.eth_held * eth_p) + (st.session_state.sol_held * sol_p) + (st.session_state.ada_held * ada_p)
    
    # Check alert limits
    btc_alert = btc_alert_active and (btc_p >= btc_high_threshold)
    eth_alert = eth_alert_active and (eth_p >= eth_high_threshold)
    sol_alert = sol_alert_active and (sol_p >= sol_high_threshold)
    ada_alert = ada_alert_active and (ada_p >= ada_high_threshold)
    
    # Render Alert Banners
    if btc_alert or eth_alert or sol_alert or ada_alert or rate_limit_active:
        alert_msgs = []
        if rate_limit_active:
            alert_msgs.append(f"⚠️ CoinGecko API Rate Limited (HTTP 429). Using cached price data. Auto-retrying in {refresh_rate}s.")
        if btc_alert:
            alert_msgs.append(f"⚠️ BITCOIN THRESHOLD EXCEEDED! Current: ${btc_p:,.2f} &ge; limit ${btc_high_threshold:,.2f}")
        if eth_alert:
            alert_msgs.append(f"⚠️ ETHEREUM THRESHOLD EXCEEDED! Current: ${eth_p:,.2f} &ge; limit ${eth_high_threshold:,.2f}")
        if sol_alert:
            alert_msgs.append(f"⚠️ SOLANA THRESHOLD EXCEEDED! Current: ${sol_p:,.2f} &ge; limit ${sol_high_threshold:,.2f}")
        if ada_alert:
            alert_msgs.append(f"⚠️ CARDANO THRESHOLD EXCEEDED! Current: ${ada_p:,.4f} &ge; limit ${ada_high_threshold:,.4f}")
        
        st.markdown(f"""
        <div class="alert-banner">
            {"<br/>".join(alert_msgs)}
        </div>
        """, unsafe_allow_html=True)
        
    # Render Grid KPI cards (Equal Height, Responsive Grid)
    btc_card_class = "kpi-card kpi-card-alert" if btc_alert else "kpi-card"
    eth_card_class = "kpi-card kpi-card-alert" if eth_alert else "kpi-card"
    sol_card_class = "kpi-card kpi-card-alert" if sol_alert else "kpi-card"
    ada_card_class = "kpi-card kpi-card-alert" if ada_alert else "kpi-card"
    
    btc_arrow = "▲" if btc_c >= 0 else "▼"
    btc_color_class = "kpi-change-up" if btc_c >= 0 else "kpi-change-down"
    eth_arrow = "▲" if eth_c >= 0 else "▼"
    eth_color_class = "kpi-change-up" if eth_c >= 0 else "kpi-change-down"
    sol_arrow = "▲" if sol_c >= 0 else "▼"
    sol_color_class = "kpi-change-up" if sol_c >= 0 else "kpi-change-down"
    ada_arrow = "▲" if ada_c >= 0 else "▼"
    ada_color_class = "kpi-change-up" if ada_c >= 0 else "kpi-change-down"
    
    st.markdown(f"""
    <div class="kpi-container">
        <!-- Bitcoin Card -->
        <div class="{btc_card_class}">
            <span class="kpi-label">Bitcoin (BTC/USD)</span>
            <div class="kpi-val" style="color: {'#ff5555' if btc_alert else '#f8f8f2'}">${btc_p:,.2f}</div>
            <span class="{btc_color_class}">{btc_arrow} {btc_c:+.2f}% (24h)</span>
        </div>
        <!-- Ethereum Card -->
        <div class="{eth_card_class}">
            <span class="kpi-label">Ethereum (ETH/USD)</span>
            <div class="kpi-val" style="color: {'#ff5555' if eth_alert else '#f8f8f2'}">${eth_p:,.2f}</div>
            <span class="{eth_color_class}">{eth_arrow} {eth_c:+.2f}% (24h)</span>
        </div>
        <!-- Solana Card -->
        <div class="{sol_card_class}">
            <span class="kpi-label">Solana (SOL/USD)</span>
            <div class="kpi-val" style="color: {'#ff5555' if sol_alert else '#f8f8f2'}">${sol_p:,.2f}</div>
            <span class="{sol_color_class}">{sol_arrow} {sol_c:+.2f}% (24h)</span>
        </div>
        <!-- Cardano Card -->
        <div class="{ada_card_class}">
            <span class="kpi-label">Cardano (ADA/USD)</span>
            <div class="kpi-val" style="color: {'#ff5555' if ada_alert else '#f8f8f2'}">${ada_p:,.4f}</div>
            <span class="{ada_color_class}">{ada_arrow} {ada_c:+.2f}% (24h)</span>
        </div>
        <!-- Connection Status / Simulation Card -->
        <div class="kpi-card">
            <span class="kpi-label">Simulator Portfolio Value</span>
            <div class="kpi-val" style="color: #bd93f9">${portfolio_value:,.2f}</div>
            <div style="display: flex; justify-content: space-between; font-size: 11px; color: #9aa0a6; font-weight: 500; margin-top: 5px;">
                <span>Status: <b>{connection_status}</b></span>
                <span>Latency: <b>{f"{latency_ms}ms" if latency_ms > 0 else "N/A"}</b></span>
            </div>
            <div style="font-size: 10px; color: #6a737d; text-align: right; margin-top: 2px;">
                Updated: <b>{now_time.strftime("%H:%M:%S")}</b>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Calculate performance metrics
    btc_held = st.session_state.btc_held
    btc_cost = st.session_state.btc_cost_basis
    btc_avg = btc_cost / btc_held if btc_held > 0 else 0.0
    btc_value = btc_held * btc_p
    btc_unrealized_pnl = btc_value - btc_cost if btc_held > 0 else 0.0
    
    eth_held = st.session_state.eth_held
    eth_cost = st.session_state.eth_cost_basis
    eth_avg = eth_cost / eth_held if eth_held > 0 else 0.0
    eth_value = eth_held * eth_p
    eth_unrealized_pnl = eth_value - eth_cost if eth_held > 0 else 0.0

    sol_held = st.session_state.sol_held
    sol_cost = st.session_state.sol_cost_basis
    sol_avg = sol_cost / sol_held if sol_held > 0 else 0.0
    sol_value = sol_held * sol_p
    sol_unrealized_pnl = sol_value - sol_cost if sol_held > 0 else 0.0

    ada_held = st.session_state.ada_held
    ada_cost = st.session_state.ada_cost_basis
    ada_avg = ada_cost / ada_held if ada_held > 0 else 0.0
    ada_value = ada_held * ada_p
    ada_unrealized_pnl = ada_value - ada_cost if ada_held > 0 else 0.0
    
    total_unrealized_pnl = btc_unrealized_pnl + eth_unrealized_pnl + sol_unrealized_pnl + ada_unrealized_pnl
    realized_pnl = st.session_state.realized_pnl
    total_net_pnl = total_unrealized_pnl + realized_pnl
    
    # Render Simplified Layout Tabs
    tab_trading, tab_charts = st.tabs(["💼 Live Portfolio & Trading", "📈 Charts & Logs"])
    
    with tab_trading:
        # Determine win/loss performance status
        if total_net_pnl > 0.01:
            status_color = "#50fa7b" # Green
            status_text = "WINNING! 🎉"
            status_icon = "🟢"
            pnl_explain = "Great job! Your trades are profitable."
        elif total_net_pnl < -0.01:
            status_color = "#ff5555" # Red
            status_text = "LOSING! 📉"
            status_icon = "🔴"
            pnl_explain = "Careful! You are currently down on your trades."
        else:
            status_color = "#f8f8f2"
            status_text = "BREAK EVEN"
            status_icon = "⚪"
            pnl_explain = "No profit or loss yet. Start trading to see your performance."
            
        roi_pct = (total_net_pnl / 100000000.0) * 100
        pnl_val_text = f"+${total_net_pnl:,.2f} (+{roi_pct:.4f}%)" if total_net_pnl >= 0 else f"-${abs(total_net_pnl):,.2f} ({roi_pct:.4f}%)"
        
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(22, 25, 37, 0.8) 0%, rgba(15, 17, 26, 0.8) 100%); padding: 22px; border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 20px; box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                <div>
                    <span style="font-size: 11px; text-transform: uppercase; color: #9aa0a6; font-weight: 600; letter-spacing: 1px;">Trading Performance Status</span>
                    <div style="font-size: 24px; font-weight: 800; font-family: 'Outfit', sans-serif; color: {status_color}; margin-top: 5px;">
                        {status_icon} {status_text}
                    </div>
                    <p style="color: #9aa0a6; font-size: 12px; margin-top: 5px; margin-bottom: 0;">{pnl_explain}</p>
                </div>
                <div style="text-align: right;">
                    <span style="font-size: 11px; text-transform: uppercase; color: #9aa0a6; font-weight: 600; letter-spacing: 1px;">Total Net Profit / Loss</span>
                    <div style="font-size: 28px; font-weight: 800; font-family: 'Outfit', sans-serif; color: {status_color}; margin-top: 5px;">
                        {pnl_val_text}
                    </div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; margin-top: 18px; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 15px; font-size: 13px;">
                <div>
                    <span style="color: #9aa0a6;">Available Cash Balance:</span>
                    <strong style="color: #f8f8f2; float: right;">${st.session_state.cash:,.2f}</strong>
                </div>
                <div>
                    <span style="color: #9aa0a6;">Unrealized P&L (Active):</span>
                    <strong style="color: {'#50fa7b' if total_unrealized_pnl >= 0 else '#ff5555'}; float: right;">
                        {f"+${total_unrealized_pnl:,.2f}" if total_unrealized_pnl >= 0 else f"-${abs(total_unrealized_pnl):,.2f}"}
                    </strong>
                </div>
                <div>
                    <span style="color: #9aa0a6;">Realized P&L (Closed Sells):</span>
                    <strong style="color: {'#50fa7b' if realized_pnl >= 0 else '#ff5555'}; float: right;">
                        {f"+${realized_pnl:,.2f}" if realized_pnl >= 0 else f"-${abs(realized_pnl):,.2f}"}
                    </strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Performance Table Metrics
        btc_pnl_pct = (btc_unrealized_pnl / btc_cost) * 100 if btc_cost > 0 else 0.0
        btc_pnl_color = "#50fa7b" if btc_unrealized_pnl >= 0 else "#ff5555"
        btc_pnl_text = f"+${btc_unrealized_pnl:,.2f} (+{btc_pnl_pct:.2f}%)" if btc_unrealized_pnl >= 0 else f"-${abs(btc_unrealized_pnl):,.2f} ({btc_pnl_pct:.2f}%)"
        
        eth_pnl_pct = (eth_unrealized_pnl / eth_cost) * 100 if eth_cost > 0 else 0.0
        eth_pnl_color = "#50fa7b" if eth_unrealized_pnl >= 0 else "#ff5555"
        eth_pnl_text = f"+${eth_unrealized_pnl:,.2f} (+{eth_pnl_pct:.2f}%)" if eth_unrealized_pnl >= 0 else f"-${abs(eth_unrealized_pnl):,.2f} ({eth_pnl_pct:.2f}%)"
        
        sol_pnl_pct = (sol_unrealized_pnl / sol_cost) * 100 if sol_cost > 0 else 0.0
        sol_pnl_color = "#50fa7b" if sol_unrealized_pnl >= 0 else "#ff5555"
        sol_pnl_text = f"+${sol_unrealized_pnl:,.2f} (+{sol_pnl_pct:.2f}%)" if sol_unrealized_pnl >= 0 else f"-${abs(sol_unrealized_pnl):,.2f} ({sol_pnl_pct:.2f}%)"

        ada_pnl_pct = (ada_unrealized_pnl / ada_cost) * 100 if ada_cost > 0 else 0.0
        ada_pnl_color = "#50fa7b" if ada_unrealized_pnl >= 0 else "#ff5555"
        ada_pnl_text = f"+${ada_unrealized_pnl:,.2f} (+{ada_pnl_pct:.2f}%)" if ada_unrealized_pnl >= 0 else f"-${abs(ada_unrealized_pnl):,.2f} ({ada_pnl_pct:.2f}%)"

        st.markdown(f"""
        <div class="performance-card">
            <table style="width:100%; border-collapse: collapse; text-align: left; font-size: 13px;">
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.08); color: #9aa0a6; font-weight: 600; text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px;">
                    <th style="padding: 10px 5px;">Asset</th>
                    <th style="padding: 10px 5px;">Amount Held</th>
                    <th style="padding: 10px 5px;">Average Buy Price</th>
                    <th style="padding: 10px 5px;">Current Live Price</th>
                    <th style="padding: 10px 5px;">Total Investment Value</th>
                    <th style="padding: 10px 5px; text-align: right;">Profit / Loss (P&L)</th>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                    <td style="padding: 12px 5px; font-weight: 600; color: #8be9fd;">Bitcoin (BTC)</td>
                    <td style="padding: 12px 5px;">{btc_held:.4f} BTC</td>
                    <td style="padding: 12px 5px;">${btc_avg:,.2f} USD</td>
                    <td style="padding: 12px 5px;">${btc_p:,.2f} USD</td>
                    <td style="padding: 12px 5px;">${btc_value:,.2f} USD</td>
                    <td style="padding: 12px 5px; text-align: right; color: {btc_pnl_color}; font-weight: 700;">{btc_pnl_text if btc_held > 0 else "No Holdings"}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                    <td style="padding: 12px 5px; font-weight: 600; color: #ff79c6;">Ethereum (ETH)</td>
                    <td style="padding: 12px 5px;">{eth_held:.4f} ETH</td>
                    <td style="padding: 12px 5px;">${eth_avg:,.2f} USD</td>
                    <td style="padding: 12px 5px;">${eth_p:,.2f} USD</td>
                    <td style="padding: 12px 5px;">${eth_value:,.2f} USD</td>
                    <td style="padding: 12px 5px; text-align: right; color: {eth_pnl_color}; font-weight: 700;">{eth_pnl_text if eth_held > 0 else "No Holdings"}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.03);">
                    <td style="padding: 12px 5px; font-weight: 600; color: #50fa7b;">Solana (SOL)</td>
                    <td style="padding: 12px 5px;">{sol_held:.4f} SOL</td>
                    <td style="padding: 12px 5px;">${sol_avg:,.2f} USD</td>
                    <td style="padding: 12px 5px;">${sol_p:,.2f} USD</td>
                    <td style="padding: 12px 5px;">${sol_value:,.2f} USD</td>
                    <td style="padding: 12px 5px; text-align: right; color: {sol_pnl_color}; font-weight: 700;">{sol_pnl_text if sol_held > 0 else "No Holdings"}</td>
                </tr>
                <tr>
                    <td style="padding: 12px 5px; font-weight: 600; color: #ffb86c;">Cardano (ADA)</td>
                    <td style="padding: 12px 5px;">{ada_held:.4f} ADA</td>
                    <td style="padding: 12px 5px;">${ada_avg:,.4f} USD</td>
                    <td style="padding: 12px 5px;">${ada_p:,.4f} USD</td>
                    <td style="padding: 12px 5px;">${ada_value:,.2f} USD</td>
                    <td style="padding: 12px 5px; text-align: right; color: {ada_pnl_color}; font-weight: 700;">{ada_pnl_text if ada_held > 0 else "No Holdings"}</td>
                </tr>
            </table>
        </div>
        """, unsafe_allow_html=True)
        
    with tab_charts:
        # Asset chart selector to handle scales elegantly
        chart_assets = st.multiselect(
            "Select assets to display on the chart:",
            ["Bitcoin", "Ethereum", "Solana", "Cardano"],
            default=["Bitcoin", "Ethereum", "Solana"]
        )

        df_history = pd.DataFrame(st.session_state.history)
        fig = go.Figure()
        
        colors = {
            "Bitcoin": "#8be9fd",
            "Ethereum": "#ff79c6",
            "Solana": "#50fa7b",
            "Cardano": "#ffb86c"
        }
        
        # Plot traces
        for asset in chart_assets:
            y_axis_id = 'y1' if asset == 'Bitcoin' else 'y2'
            fig.add_trace(go.Scatter(
                x=df_history['Time'],
                y=df_history[asset],
                name=asset,
                line=dict(color=colors[asset], width=3),
                mode='lines',
                yaxis=y_axis_id
            ))
            
        btc_selected = "Bitcoin" in chart_assets
        others_selected = any(x in chart_assets for x in ["Ethereum", "Solana", "Cardano"])
        
        layout_args = dict(
            template='plotly_dark',
            paper_bgcolor='#07090e',
            plot_bgcolor='#0f111a',
            hovermode='x unified',
            margin=dict(l=40, r=40, t=10, b=30),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.04)',
                zeroline=False
            )
        )
        
        if btc_selected:
            btc_min, btc_max = df_history['Bitcoin'].min(), df_history['Bitcoin'].max()
            btc_padding = (btc_max - btc_min) * 0.05 if btc_max != btc_min else 20
            layout_args['yaxis'] = dict(
                title=dict(text="Bitcoin ($USD)", font=dict(color='#8be9fd')),
                tickfont=dict(color='#8be9fd'),
                gridcolor='rgba(255, 255, 255, 0.04)',
                range=[btc_min - btc_padding, btc_max + btc_padding],
                side="left"
            )
            
        if others_selected:
            active_cols = [x for x in ["Ethereum", "Solana", "Cardano"] if x in chart_assets]
            combined_min = df_history[active_cols].min().min()
            combined_max = df_history[active_cols].max().max()
            combined_padding = (combined_max - combined_min) * 0.05 if combined_max != combined_min else 2
            
            layout_args['yaxis2'] = dict(
                title=dict(text="Other Assets ($USD)", font=dict(color='#ff79c6')),
                tickfont=dict(color='#ff79c6'),
                range=[combined_min - combined_padding, combined_max + combined_padding],
                overlaying="y",
                side="right",
                showgrid=False if btc_selected else True
            )
            
        fig.update_layout(**layout_args)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Transaction logs
        st.markdown("""
        <div style="margin-top: 15px; margin-bottom: 12px;">
            <h4 style="font-family: 'Outfit', sans-serif; font-weight: 600; font-size: 13px; text-transform: uppercase; color: #bd93f9; letter-spacing: 0.5px;">
                📜 Recent Transactions Log
            </h4>
        </div>
        """, unsafe_allow_html=True)
        
        if len(st.session_state.trades_log) > 0:
            logs_html = "".join([f"<div style='font-family: monospace; font-size: 12px; margin-bottom: 6px;'>{log}</div>" for log in st.session_state.trades_log[-5:]])
            st.markdown(f"""
            <div style="background-color: #0f111a; border: 1px solid rgba(255,255,255,0.05); padding: 15px; border-radius: 10px; max-height: 150px; overflow-y: auto;">
                {logs_html}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No trades executed in this session yet.")
            
        # Export CSV Button
        if len(st.session_state.history) > 0:
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
            df_download = pd.DataFrame(st.session_state.history)
            csv_data = df_download.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export Session Price History (CSV)",
                data=csv_data,
                file_name="westeros_price_history.csv",
                mime="text/csv",
                key="download_price_history_btn"
            )

# Render Live View inside Fragment
render_live_view()
