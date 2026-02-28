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
st.set_page_config(page_title="NIFTY 50 ARIMA Analyzer", page_icon="🏛️", layout="wide")

st.title("🏛️ NIFTY 50 Forecast Table & Analysis")
st.markdown("Select an ARIMA model to generate a 15-day forecast table for NIFTY 50 stocks.")

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
st.sidebar.header("Data Settings")
selected_name = st.sidebar.selectbox("Choose a Company", options=list(nifty50_dict.keys()))
ticker = nifty50_dict[selected_name]
period = st.sidebar.selectbox("History Period", options=["6mo", "1y", "2y"], index=1)

st.sidebar.header("Model Selection")
# Option to select between ARIMA(1,1,1) and ARIMA(2,1,2)
model_choice = st.sidebar.radio("Select ARIMA Order", ("ARIMA(1,1,1)", "ARIMA(2,1,2)"))
arima_order = (1, 1, 1) if model_choice == "ARIMA(1,1,1)" else (2, 1, 2)

# 4. PDF GENERATION FUNCTION
def create_pdf(df, ticker_name, model_name, forecast_df, fig):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Financial Analysis Report: {ticker_name}")
    p.setFont("Helvetica", 12)
    p.drawString(100, 730, f"Model Used: {model_name}")
    p.drawString(100, 715, f"Latest Closing Price: ₹{df['Close'].iloc[-1]:,.2f}")

    # Chart Image
    try:
        img_bytes = fig.to_image(format="png", width=600, height=300)
        p.drawImage(ImageReader(io.BytesIO(img_bytes)), 50, 380, width=500, height=250)
    except:
        p.drawString(100, 450, "Chart could not be rendered in PDF.")

    # Forecast Table in PDF
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, 350, "15-Day Forecast Table")
    p.setFont("Helvetica", 10)
    
    y = 330
    p.drawString(120, y, "Date")
    p.drawString(250, y, "Predicted Price (₹)")
    p.line(100, y-5, 500, y-5)
    
    y -= 20
    for index, row in forecast_df.iterrows():
        if y < 50: # New page if table is too long
            p.showPage()
            y = 750
        p.drawString(120, y, row['Date'].strftime('%Y-%m-%d'))
        p.drawString(250, y, f"{row['Predicted Price']:,.2f}")
        y -= 15

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# 5. DATA FETCHING
@st.cache_data
def get_live_data(symbol, time_period):
    data = yf.download(symbol, period=time_period)
    data = data.reset_index()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] for col in data.columns]
    return data

df = get_live_data(ticker, period)

if not df.empty:
    # 6. PLOTTING (Actual Price Only)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], name='Actual Price', line=dict(color='#00d1ff', width=2)))
    
    fig.update_layout(
        template="plotly_dark", 
        title=f"Historical Price: {selected_name}",
        xaxis_title="Date",
        yaxis_title="Closing Price (₹)",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 7. FORECASTING & TABLE
    st.write("---")
    st.subheader(f"15-Day Forecast Results ({model_choice})")
    
    with st.spinner(f"Calculating {model_choice}..."):
        try:
            model = ARIMA(df['Close'], order=arima_order)
            model_fit = model.fit()
            forecast_steps = 15
            forecast = model_fit.forecast(steps=forecast_steps)
            
            # Generate future dates
            last_date = df['Date'].max()
            future_dates = [last_date + datetime.timedelta(days=i) for i in range(1, forecast_steps + 1)]
            
            # Create the forecast dataframe for the table
            forecast_df = pd.DataFrame({
                'Date': future_dates,
                'Predicted Price': forecast
            })
            
            # Display Table in App
            st.table(forecast_df.style.format({'Predicted Price': '{:,.2f}'}))

            # 8. REPORT GENERATION
            if st.button("Generate & Download PDF Report"):
                pdf_data = create_pdf(df, selected_name, model_choice, forecast_df, fig)
                st.download_button(
                    label="📥 Click here to Save PDF",
                    data=pdf_data,
                    file_name=f"{selected_name}_Forecast.pdf",
                    mime="application/pdf"
                )
                
        except Exception as e:
            st.error(f"Model Error: {e}")

else:
    st.error("Failed to retrieve data.")
