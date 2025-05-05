import streamlit as st
from graph_agent import run_financial_agent
from utils_plot import price_chart, rsi_chart

st.set_page_config(page_title="AI Financial Analyst", layout="wide")

st.title("📈 AI‑Powered Financial Analyst")
ticker = st.text_input("Ticker (e.g. AAPL)", value="AAPL")
company = st.text_input("Company name", value="Apple Inc.")

if st.button("Analyze"):
    with st.spinner("Crunching numbers…"):
        analysis, df = run_financial_agent(company, ticker.upper())

    st.subheader("AI Analysis")
    st.markdown(analysis)

    st.subheader("Charts")
    st.plotly_chart(price_chart(df), use_container_width=True)
    st.plotly_chart(rsi_chart(df),   use_container_width=True)

    st.info("Disclaimer: Information is for educational purposes only and **not** personalized investment advice.")