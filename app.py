import streamlit as st
import pandas as pd
import plotly.express as px
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# 1. PAGE SETUP
st.set_page_config(page_title="PRICE CHART", page_icon="📈", layout="wide")

# 2. TITLE & DESCRIPTION
st.title("📊 PRICE CHART")
st.markdown("""
This dashboard visualizes the historical price data from **PriceData.csv**. 
You can hover over the chart to see exact prices and zoom into specific date ranges.
""")

# 3. PDF GENERATION FUNCTION
def create_pdf(df, price_col):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Price Analysis Report")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, 730, f"Analysis for column: {price_col}")
    
    # Getting the latest price as a number
    val = df[price_col].iloc[-1]
    p.drawString(100, 715, f"Latest Price recorded: {float(val):,.2f}")
    
    p.drawString(100, 680, "Summary Data (Last 5 entries):")
    y_position = 660
    for i in range(1, 6):
        if i <= len(df):
            row = df.iloc[-i]
            date_str = row['Date'].strftime('%Y-%m-%d')
            price_val = float(row[price_col])
            text = f"Date: {date_str} | Price: {price_val:,.2f}"
            p.drawString(120, y_position, text)
            y_position -= 20
        
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# 4. DATA LOADING (WITH CLEANING FIX)
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('PriceData.csv')
        
        # FIX 1: Remove hidden spaces from column names
        df.columns = df.columns.str.strip()
        
        # FIX 2: Convert Price to float (Remove commas first)
        # Finds the price column automatically
        price_col = [c for c in df.columns if 'Price' in c or 'Close' in c][0]
        df[price_col] = df[price_col].astype(str).str.replace(',', '').astype(float)
        
        # FIX 3: Convert Date
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], format='mixed')
            df = df.sort_values(by='Date')
            
        return df
    except Exception as e:
        st.error(f"Error loading PriceData.csv: {e}")
        return None

df = load_data()

# 5. DASHBOARD LOGIC
if df is not None:
    # Auto-detect price column again for plotting
    price_cols = [c for c in df.columns if 'Price' in c or 'Close' in c]
    
    if 'Date' in df.columns and len(price_cols) > 0:
        target_y = price_cols[0]

        # --- THE CHART ---
        fig = px.line(
            df, x='Date', y=target_y, 
            title=f"Historical Trend: {target_y}",
            template="plotly_dark"
        )
        fig.update_traces(line=dict(color='#00d1ff', width=2))
        st.plotly_chart(fig, use_container_width=True)

        # --- PDF BUTTON ---
        st.write("---")
        st.subheader("Export Analysis")
        
        # Creating the PDF with the cleaned numeric data
        pdf_data = create_pdf(df, target_y)
        
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_data,
            file_name="Price_Report.pdf",
            mime="application/pdf"
        )
            
    else:
        st.warning("Ensure PriceData.csv has 'Date' and a 'Price' column.")

st.markdown("---")
st.caption("PRICE CHART | Automated Report Generator")
