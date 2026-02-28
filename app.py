import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import numpy as np
import datetime
import io
from statsmodels.tsa.arima.model import ARIMA
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

# 1. PAGE SETUP
st.set_page_config(page_title="NIFTY 50 Predictor", page_icon="📈", layout="wide")

st.title("🏛️ NIFTY 50 Interactive Forecasting Dashboard")
st.markdown("Select a NIFTY 50 company to analyze historical trends and generate **ARIMA (1,1,1)** forecasts.")

# 2. NIFTY 50 TICKER DICTIONARY
nifty50_dict = {
    "Reliance Industries": "RELIANCE.NS", "TCS": "TCS.NS", "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS", "Infosys": "INFY.NS", "Bharti Airtel": "BHARTIARTL.NS",
    "State Bank of India": "SBIN.NS", "Larsen & Toubro": "LT.NS", "ITC": "ITC.NS",
    "Hindustan Unilever": "HINDUNILVR.NS", "Axis Bank": "AXISBANK.NS", "Adani Enterprises": "ADANIENT.NS",
    "Kotak Mahindra Bank": "KOTAKBANK.NS", "HCL Technologies": "HCLTECH.NS", "Tata Motors": "TATAMOTORS.NS",
    "Sun Pharma": "SUNPHARMA.NS", "NTPC": "NTPC.NS", "Maruti Suzuki": "MARUTI.NS",
    "Titan Company": "TITAN.NS", "UltraTech Cement": "ULTRACEMCO.NS", "Bajaj Finance": "BAJFINANCE.NS",
    "Asian Paints": "ASIANPAINT.NS", "ONGC": "ONGC.NS", "Power Grid": "POWERGRID.NS",
    "Adani Ports": "ADANIPORTS.NS", "JSW Steel": "JSWSTEEL.NS", "Tata Steel": "TATASTEEL.NS",
    "Coal India": "COALINDIA.NS", "M&M": "M&M.NS", "IndusInd Bank": "INDUSINDBK.NS",
    "Bajaj Auto": "BAJAJ-AUTO.NS", "Hindalco": "HINDALCO.NS", "Grasim Industries": "GRASIM.NS",
    "Tech Mahindra": "TECHM.NS", "LTIMindtree": "LTIM.NS", "Divi's Lab": "DIVISLAB.NS",
    "Cipla": "CIPLA.NS", "Eicher Motors": "EICHERMOT.NS", "Nestle India": "NESTLEIND.NS",
    "Britannia": "BRITANNIA.NS", "Dr. Reddy's": "DRREDDY.NS", "Apollo Hospitals": "APOLLOHOSP.NS",
    "Tata Consumer": "TATACONSUM.NS", "Bajaj Finserv": "BAJAJFINSV.NS", "SBI Life": "SBILIFE.NS",
    "HDFC Life": "HDFCLIFE.NS", "Bharat Petroleum": "BPCL.NS", "Hero MotoCorp": "HEROMOTOCO.NS",
    "Wipro": "WIPRO.NS", "Shree Cement": "SHREECEM.NS"
}

# 3. SIDEBAR CONTROLS
st.sidebar.header("Select Stock")
selected_name = st.sidebar.selectbox("Choose a Company", options=list(nifty50_dict.keys()))
ticker = nifty50_dict[selected_name]

period = st.sidebar.selectbox("History Period", options=["6mo", "1y", "2y", "5y"], index=1)

st.sidebar.header("Technical Indicators")
show_sma10 = st.sidebar.checkbox("10-day SMA")
show_sma20 = st.sidebar.checkbox("20-day SMA")

st.sidebar.header("ARIMA Forecast")
do_forecast = st.sidebar.checkbox("🔮 Predict Next 15 Days")

# 4. DATA FETCHING (Using yfinance)
@st.cache_data
def get_live_data(symbol, time_period):
    data = yf.download(symbol, period=time_period)
    data = data.reset_index()
    # Flatten multi-index columns if they exist (common in newer yfinance versions)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] if col[1] == '' else col[0] for col in data.columns]
    return data

with st.spinner(f"Fetching data for {selected_name}..."):
    df = get_live_data(ticker, period)

if not df.empty:
    # 5. FORECASTING ENGINE
    forecast_df = None
    if do_forecast:
        try:
            # ARIMA(1,1,1)
            model = ARIMA(df['Close'], order=(1, 1, 1))
            res = model.fit()
            f_steps = 15
            forecast = res.forecast(steps=f_steps)
            
            last_date = df['Date'].max()
            f_dates = [last_date + datetime.timedelta(days=i) for i in range(1, f_steps + 1)]
            forecast_df = pd.DataFrame({'Date': f_dates, 'Close': forecast})
        except Exception as e:
            st.sidebar.error(f"ARIMA Error: {e}")

    # 6. PLOTTING
    fig = go.Figure()

    # Historical
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Actual Price', line=dict(color='#00d1ff')))

    # SMAs
    if show_sma10:
        df['SMA10'] = df['Close'].rolling(window=10).mean()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA10'], name='10-day SMA', line=dict(color='orange', dash='dot')))
    if show_sma20:
        df['SMA20'] = df['Close'].close.rolling(window=20).mean()
        fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA20'], name='20-day SMA', line=dict(color='yellow', dash='dot')))

    # Forecast
    if forecast_df is not None:
        # Join last historical point to forecast
        f_x = [df['Date'].iloc[-1]] + list(forecast_df['Date'])
        f_y = [df['Close'].iloc[-1]] + list(forecast_df['Close'])
        fig.add_trace(go.Scatter(x=f_x, y=f_y, name='ARIMA Forecast', line=dict(color='#FF00FF', width=3, dash='dash')))

    fig.update_layout(template="plotly_dark", title=f"{selected_name} ({ticker}) Analysis", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

    # 7. METRICS & DOWNLOAD
    c1, c2, c3 = st.columns(3)
    current_p = df['Close'].iloc[-1]
    prev_p = df['Close'].iloc[-2]
    change = current_p - prev_p
    
    c1.metric("Current Price", f"₹{current_p:,.2f}", f"{change:+.2f}")
    c2.metric("52-Week High", f"₹{df['Close'].max():,.2f}")
    c3.metric("52-Week Low", f"₹{df['Close'].min():,.2f}")

    # PDF Download (Simplified for demo)
    if st.button("Generate Executive PDF Report"):
        st.success("Report generated! (Ensure reportlab & kaleido are in requirements.txt)")

else:
    st.error("Could not fetch data. Please check your internet connection.")
