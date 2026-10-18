"""Výpočet technických indikátorov: SMA, RSI."""

import pandas as pd


def sma(series: pd.Series, window: int) -> pd.Series:
    """Jednoduchý kĺzavý priemer (Simple Moving Average)."""
    return series.rolling(window=window).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def add_all_indicators(df: pd.DataFrame, sma_short: int, sma_long: int, rsi_period: int) -> pd.DataFrame:
    """Pridá do DataFrame stĺpce so všetkými indikátormi."""
    df = df.copy()
    df["SMA_short"] = sma(df["Close"], sma_short)
    df["SMA_long"] = sma(df["Close"], sma_long)
    df["RSI"] = rsi(df["Close"], rsi_period)
    return df
