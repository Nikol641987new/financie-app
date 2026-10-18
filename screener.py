"""Vyhodnotenie signálov (BUY/SELL) na základe indikátorov a pravidiel."""

from dataclasses import dataclass
from typing import Optional
import pandas as pd

from indicators import add_all_indicators


@dataclass
class Signal:
    ticker: str
    signal_type: str  # "BUY" alebo "SELL"
    reason: str
    price: float


def evaluate_ticker(
    ticker: str,
    df: pd.DataFrame,
    sma_short: int,
    sma_long: int,
    rsi_period: int,
    rsi_oversold: float,
    rsi_overbought: float,
    stop_loss_pct: float = 0,
    take_profit_pct: float = 0,
    purchase_price: Optional[float] = None,
) -> list[Signal]:
    """
    Vyhodnotí jeden ticker podľa všetkých nastavených pravidiel.
    Vráti zoznam signálov (môže byť prázdny, jeden, alebo viac).
    """
    signals: list[Signal] = []

    df = add_all_indicators(df, sma_short, sma_long, rsi_period)
    if len(df) < 2:
        return signals

    latest = df.iloc[-1]
    previous = df.iloc[-2]
    current_price = float(latest["Close"])

    # --- 1. Golden Cross / Death Cross (SMA prekríženie) ---
    if pd.notna(latest["SMA_short"]) and pd.notna(latest["SMA_long"]) and pd.notna(previous["SMA_short"]) and pd.notna(previous["SMA_long"]):
        crossed_up = previous["SMA_short"] <= previous["SMA_long"] and latest["SMA_short"] > latest["SMA_long"]
        crossed_down = previous["SMA_short"] >= previous["SMA_long"] and latest["SMA_short"] < latest["SMA_long"]

        if crossed_up:
            signals.append(Signal(
                ticker=ticker,
                signal_type="BUY",
                reason=f"Golden Cross: SMA{sma_short} prekrížil SMA{sma_long} smerom hore",
                price=current_price,
            ))
        elif crossed_down:
            signals.append(Signal(
                ticker=ticker,
                signal_type="SELL",
                reason=f"Death Cross: SMA{sma_short} prekrížil SMA{sma_long} smerom dole",
                price=current_price,
            ))

    # --- 2. RSI prekúpenosť / prepredanosť ---
    if pd.notna(latest["RSI"]):
        if latest["RSI"] < rsi_oversold:
            signals.append(Signal(
                ticker=ticker,
                signal_type="BUY",
                reason=f"RSI={latest['RSI']:.1f} je pod hranicou prepredanosti ({rsi_oversold})",
                price=current_price,
            ))
        elif latest["RSI"] > rsi_overbought:
            signals.append(Signal(
                ticker=ticker,
                signal_type="SELL",
                reason=f"RSI={latest['RSI']:.1f} je nad hranicou prekúpenosti ({rsi_overbought})",
                price=current_price,
            ))

    # --- 3. Stop-loss / Take-profit (len ak je zadaná nákupná cena) ---
    if purchase_price:
        change_pct = (current_price - purchase_price) / purchase_price * 100

        if stop_loss_pct and change_pct <= -abs(stop_loss_pct):
            signals.append(Signal(
                ticker=ticker,
                signal_type="SELL",
                reason=f"Stop-loss: cena klesla o {change_pct:.1f}% od nákupnej ceny {purchase_price}",
                price=current_price,
            ))

        if take_profit_pct and change_pct >= abs(take_profit_pct):
            signals.append(Signal(
                ticker=ticker,
                signal_type="SELL",
                reason=f"Take-profit: zisk {change_pct:.1f}% od nákupnej ceny {purchase_price}",
                price=current_price,
            ))

    return signals
