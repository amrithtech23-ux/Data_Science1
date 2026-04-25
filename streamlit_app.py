import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import io

st.set_page_config(page_title="Provision Shop Sales Analyzer", layout="wide")
st.title("🏪 Provision Shop Sales Analyzer")

# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = None
if "analysis_ready" not in st.session_state:
    st.session_state.analysis_ready = False
if "selected_product" not in st.session_state:
    st.session_state.selected_product = None

# 1. Upload
uploaded = st.file_uploader("Upload Sales Data (.txt/.csv)", type=["txt", "csv"])
delimiter = st.text_input("Delimiter", ",", max_chars=1)

if st.button("🧹 Clean Data") and uploaded:
    try:
        raw = uploaded.read().decode("utf-8")
        # Read with headers
        df = pd.read_csv(io.StringIO(raw), delimiter=delimiter)
        
        # Clean: remove rows with missing values in numeric columns, clip negatives
        month_cols = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                      'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        
        # Convert month columns to numeric
        for col in month_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with all NaN in month columns
        df = df.dropna(subset=month_cols, how='all')
        
        # Fill remaining NaN with 0
        for col in month_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0).clip(lower=0)
        
        st.session_state.df = df.reset_index(drop=True)
        st.session_state.analysis_ready = False
        st.success(f"✅ Data cleaned! Found {len(st.session_state.df)} products")
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")

# 2. Cleaned Data Display & Export
if st.session_state.df is not None:
    st.subheader("📋 Cleaned Data")
    st.dataframe(st.session_state.df, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        csv_data = st.session_state.df.to_csv(index=False)
        st.download_button("📥 Export Cleaned Data", csv_data, "cleaned_sales.csv", "text/csv")
    with col2:
        st.file_uploader("🔄 Upload Cleaned Data (Optional)", type=["csv", "txt"], key="clean_upload")
    
    # Product Selection
    if 'product_name' in st.session_state.df.columns:
        products = st.session_state.df['product_name'].tolist()
        selected_product = st.selectbox("Select Product to Analyze", products)
        st.session_state.selected_product = selected_product
        
        # Filter data for selected product
        product_row = st.session_state.df[st.session_state.df['product_name'] == selected_product].iloc[0]
        
        # 3. Line Graph
        if st.button("📈 Line Graph Sales Detail"):
            month_cols = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                           'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            sales_data = [product_row[col] for col in month_cols]
            
            chart_data = pd.DataFrame({
                'Month': month_names,
                'Sales': sales_data
            }).set_index('Month')
            st.line_chart(chart_data, use_container_width=True)

    # 4. Data Analysis
    st.subheader("📊 Data Analysis")
    c1, c2, c3 = st.columns(3)
    
    if c1.button("1. Summaries"):
        st.session_state.analysis_ready = True
        month_cols = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                      'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        numeric_df = st.session_state.df[month_cols]
        st.write("**Overall Sales Summary:**")
        st.write(numeric_df.describe())
        
    if c2.button("2. Tables"):
        st.session_state.analysis_ready = True
        st.dataframe(st.session_state.df, use_container_width=True)
        
    if c3.button("3. Charts"):
        st.session_state.analysis_ready = True
        if 'product_name' in st.session_state.df.columns:
            month_cols = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            chart_df = st.session_state.df.set_index('product_name')[month_cols].T
            st.bar_chart(chart_df, use_container_width=True)

    # 5. Predictions & Recommendations
    if st.button("🔮 Data Analytics", disabled=not st.session_state.analysis_ready, type="primary"):
        if st.session_state.selected_product and 'product_name' in st.session_state.df.columns:
            product_row = st.session_state.df[st.session_state.df['product_name'] == st.session_state.selected_product].iloc[0]
            month_cols = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                          'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
            sales_data = [product_row[col] for col in month_cols]
            
            X = np.arange(len(sales_data)).reshape(-1, 1)
            y = np.array(sales_data)
            model = LinearRegression().fit(X, y)
            preds = [round(p, 2) for p in model.predict(np.arange(len(sales_data), len(sales_data)+3).reshape(-1, 1))]
            slope = model.coef_[0]
            
            if slope > 10:
                trend, recs = "📈 Increasing", [
                    f"Increase inventory stock for {st.session_state.selected_product}.",
                    "Negotiate bulk supplier discounts for better margins.",
                    "Consider promotional offers to sustain growth."
                ]
            elif slope < -10:
                trend, recs = "📉 Decreasing", [
                    f"Review pricing strategy for {st.session_state.selected_product}.",
                    "Launch targeted promotions or bundle deals.",
                    "Analyze competitor pricing and customer feedback."
                ]
            else:
                trend, recs = "➡️ Stable", [
                    "Maintain current inventory levels.",
                    "Focus on customer retention strategies.",
                    "Monitor seasonal trends for opportunities."
                ]
            
            st.text_area("Predictions & Recommendations", 
                         f"Product: {st.session_state.selected_product}\n\n"
                         f"TREND: {trend}\n"
                         f"Growth Rate: {slope:.2f} units/month\n\n"
                         f"PREDICTIONS (Next 3 months): {preds[0]} → {preds[1]} → {preds[2]}\n\n"
                         f"RECOMMENDATIONS:\n" + "\n".join(f"• {r}" for r in recs),
                         height=250, disabled=True)
        else:
            st.warning("Please select a product to analyze")
