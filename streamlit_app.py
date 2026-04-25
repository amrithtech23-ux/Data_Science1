import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import io

st.set_page_config(page_title="Provision Shop Analytics", layout="wide")
st.title("🏪 Provision Shop Sales Analyzer")

# Initialize session state
if "df" not in st.session_state: st.session_state.df = None
if "analysis_ready" not in st.session_state: st.session_state.analysis_ready = False

# 1. Upload
uploaded = st.file_uploader("Upload Sales Data (.txt/.csv)", type=["txt", "csv"])
delimiter = st.text_input("Delimiter", ",", max_chars=1)

if st.button(" Clean Data") and uploaded:
    raw = uploaded.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw), delimiter=delimiter, header=None, names=["period", "sales"])
    df["sales"] = pd.to_numeric(df["sales"], errors="coerce").clip(lower=0)
    st.session_state.df = df.dropna().drop_duplicates().reset_index(drop=True)
    st.session_state.analysis_ready = False
    st.success("✅ Data cleaned!")

# 2. Cleaned Data Display & Export
if st.session_state.df is not None:
    st.subheader(" Cleaned Data")
    st.text_area("", st.session_state.df.to_string(index=False), height=120, disabled=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("📥 Export Cleaned Data", st.session_state.df.to_csv(index=False), "cleaned_sales.csv", "text/csv")
    with col2:
        st.file_uploader("🔄 Upload Cleaned Data (Optional)", type=["csv", "txt"], key="clean_upload")

    # 3. Line Graph
    if st.button("📈 Line Graph Sales Detail"):
        chart_df = st.session_state.df.set_index("period")
        st.line_chart(chart_df, use_container_width=True)

    # 4. Data Analysis
    st.subheader("📊 Data Analysis")
    c1, c2, c3 = st.columns(3)
    if c1.button("1. Summaries"): st.session_state.analysis_ready = True; st.write(st.session_state.df["sales"].describe())
    if c2.button("2. Tables"): st.session_state.analysis_ready = True; st.dataframe(st.session_state.df, use_container_width=True)
    if c3.button("3. Charts"): st.session_state.analysis_ready = True; st.bar_chart(st.session_state.df.set_index("period"), use_container_width=True)

    # 5. Predictions & Recommendations
    if st.button(" Data Analytics", disabled=not st.session_state.analysis_ready, type="primary"):
        df = st.session_state.df
        X = np.arange(len(df)).reshape(-1, 1)
        y = df["sales"].values
        model = LinearRegression().fit(X, y)
        preds = [round(p, 2) for p in model.predict(np.arange(len(df), len(df)+3).reshape(-1, 1))]
        slope = model.coef_[0]
        
        if slope > 50: trend, recs = "📈 Increasing", ["Increase inventory for upcoming periods.", "Negotiate bulk supplier discounts."]
        elif slope < -50: trend, recs = "📉 Decreasing", ["Launch targeted promotions.", "Review pricing & product mix."]
        else: trend, recs = "➡️ Stable", ["Maintain current stock levels.", "Focus on customer retention."]
        
        st.text_area("Predictions & Recommendations", 
                     f"TREND: {trend}\nPREDICTIONS (Next 3): {preds}\n\nRECOMMENDATIONS:\n" + "\n".join(f"{i+1}. {r}" for i,r in enumerate(recs)),
                     height=150, disabled=True)
