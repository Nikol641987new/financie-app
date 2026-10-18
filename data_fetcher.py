"""Sťahovanie historických cenových dát pre zadané tickery."""

import yfinance as yf
import pandas as pd


def fetch_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Stiahne historické dáta pre daný ticker.

    Args:
        ticker: napr. "AAPL"
        period: časové obdobie ("1y", "6mo", "2y"...)
        interval: interval sviečok ("1d", "1h"...)

    Returns:
        DataFrame so stĺpcami Open, High, Low, Close, Volume
    """
    data = yf.Ticker(ticker).history(period=period, interval=interval)
    if data.empty:
        raise ValueError(f"Nepodarilo sa stiahnuť dáta pre ticker '{ticker}'")
    return data


def fetch_latest_price(ticker: str) -> float:
    """Vráti poslednú dostupnú cenu pre ticker."""
    data = fetch_history(ticker, period="5d")
    return float(data["Close"].iloc[-1])
