import streamlit as st
import pandas as pd
import plotly.express as px
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader

# 1. PAGE SETUP
st.set_page_config(page_title="Universal Price Chart", page_icon="📈", layout="wide")

# 2. TITLE & DESCRIPTION
st.title("📊 Universal Price Analysis Tool")
st.markdown("""
**How to use:**
1. Upload any CSV file containing a **Date** column and a **Price/Close** column.
2. View the interactive chart and summary.
3. Generate and download a PDF report including the visual chart.
""")

# 3. PDF GENERATION FUNCTION
def create_pdf(df, price_col, fig):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    
    # Title & Metadata
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, "Custom Price Analysis Report")
    p.setFont("Helvetica", 12)
    p.drawString(100, 725, f"Data Column: {price_col}")
    latest_val = df[price_col].iloc[-1]
    p.drawString(100, 710, f"Latest Value: {float(latest_val):,.2f}")

    # --- ADD THE CHART IMAGE ---
    try:
        img_bytes = fig.to_image(format="png", width=600, height=350)
        img_reader = ImageReader(io.BytesIO(img_bytes))
        p.drawImage(img_reader, 50, 330, width=500, height=300)
    except Exception as e:
        p.drawString(100, 450, f"(Chart could not be rendered in PDF: {e})")

    # Table Summary
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, 300, "Recent Data Summary:")
    p.setFont("Helvetica", 10)
    y_position = 280
    for i in range(1, 6):
        if i <= len(df):
            row = df.iloc[-i]
            date_str = row['Date'].strftime('%Y-%m-%d') if isinstance(row['Date'], pd.Timestamp) else str(row['Date'])
            price_val = float(row[price_col])
            text = f"Date: {date_str} | Price: {price_val:,.2f}"
            p.drawString(120, y_position, text)
            y_position -= 18
        
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# 4. FILE UPLOADER SECTION
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    try:
        # Load the uploaded file
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip() # Clean column names
        
        # Identify Date Column
        date_col = next((c for c in df.columns if 'Date' in c or 'Time' in c), None)
        # Identify Price Column
        price_col = next((c for c in df.columns if any(k in c for k in ['Price', 'Close', 'Val', 'Amt'])), None)

        if date_col and price_col:
            # Data Cleaning: Remove commas and convert to numbers
            df[price_col] = df[price_col].astype(str).str.replace(',', '', regex=False).astype(float)
            df[date_col] = pd.to_datetime(df[date_col], format='mixed')
            df = df.sort_values(by=date_col)

            # 5. DISPLAY CHART
            fig = px.line(
                df, x=date_col, y=price_col, 
                title=f"Trend Analysis: {price_col} over {date_col}",
                template="plotly_dark"
            )
            fig.update_traces(line=dict(color='#00d1ff', width=2))
            st.plotly_chart(fig, use_container_width=True)

            # 6. EXPORT SECTION
            st.write("---")
            st.subheader("Generate Report")
            if st.button("Prepare PDF for Download"):
                with st.spinner("Processing your data..."):
                    pdf_data = create_pdf(df, price_col, fig)
                    st.download_button(
                        label="💾 Download PDF Report",
                        data=pdf_data,
                        file_name="My_Price_Report.pdf",
                        mime="application/pdf"
                    )
        else:
            st.error(f"Could not find required columns. Found: {list(df.columns)}")
            st.info("Make sure your file has a column with 'Date' and one with 'Price' or 'Close' in the header.")

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("👆 Please upload a CSV file to get started.")

st.markdown("---")
st.caption("Custom Analytics Dashboard | Built with Streamlit & Plotly")
