# data_retrieval.py

import os
import requests
import pandas as pd
import yfinance as yf
import pandas_ta as ta
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY   = os.getenv("FMP_API_KEY")
SERPAPI_KEY   = os.getenv("SERPAPI_API_KEY")

# ---------- News -------------------------------------------------------------

def get_company_news(query: str, n: int = 5):
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "tbm": "nws",
        "num": n,
        "api_key": SERPAPI_KEY
    }
    try:
        return requests.get(url, params=params, timeout=10) \
                       .json() \
                       .get("news_results", [])
    except Exception:
        return []

# ---------- Price history ---------------------------------------------------

def get_stock_data(ticker: str, period="6mo", interval="1d") -> pd.DataFrame:
    df = yf.Ticker(ticker) \
           .history(period=period, interval=interval, auto_adjust=True)
    # ensure DateTimeIndex and also keep a 'date' column
    df.index = pd.to_datetime(df.index)
    df["date"] = df.index
    return df.reset_index(drop=True)

# ---------- Technical indicators -------------------------------------------

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # ensure a DatetimeIndex for pandas_ta
    if "date" in df.columns:
        df.index = pd.to_datetime(df["date"])
    elif not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # compute indicators
    df["rsi"]  = ta.rsi(df["Close"], length=14)
    macd = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    df = pd.concat([df, macd], axis=1)
    df["vwap"] = ta.vwap(
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        volume=df["Volume"]
    )

    # if you need 'date' column again after setting index:
    df["date"] = df.index
    return df.reset_index(drop=True)

# ---------- Financial statements & ratios ---------------------------------

FMP_BASE = "https://financialmodelingprep.com/api/v3"

def _fmp(endpoint: str):
    url = f"{FMP_BASE}/{endpoint}&apikey={FMP_API_KEY}"
    return requests.get(url, timeout=15).json()

def get_financial_statements(ticker: str) -> dict:
    return {
        "income":  pd.DataFrame(_fmp(f"income-statement/{ticker}?limit=5")),
        "balance": pd.DataFrame(_fmp(f"balance-sheet-statement/{ticker}?limit=5")),
        "cash":    pd.DataFrame(_fmp(f"cash-flow-statement/{ticker}?limit=5")),
        "quote":   _fmp(f"quote/{ticker}?limit=1")[0]   # current price & PE
    }

def compute_ratios(stmts: dict) -> dict:
    inc, bal = stmts["income"].iloc[0], stmts["balance"].iloc[0]
    price    = stmts["quote"]["price"]
    eps      = inc.get("eps")
    ratios   = {
        "pe_ratio":        round(price/eps, 2) if eps else None,
        "debt_to_equity":  round(bal["totalDebt"] / bal["totalStockholdersEquity"], 2),
        "profit_margin":   round(inc["netIncome"] / inc["revenue"], 2)
    }
    return ratios
