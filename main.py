"""
Hlavný skript: stiahne dáta pre všetky tickery z config.yaml,
vyhodnotí signály a pošle notifikácie.

Spustenie: python main.py
"""

import yaml

from data_fetcher import fetch_history
from screener import evaluate_ticker
from notifier import notify_signals


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    config = load_config()

    tickers = config["tickers"]
    ind_cfg = config["indicators"]
    rules_cfg = config.get("rules", {})
    purchase_prices = config.get("purchase_prices", {}) or {}

    all_signals = []

    for ticker in tickers:
        print(f"Spracúvam {ticker}...")
        try:
            df = fetch_history(ticker, period="1y")
        except Exception as e:
            print(f"  Chyba pri sťahovaní dát pre {ticker}: {e}")
            continue

        signals = evaluate_ticker(
            ticker=ticker,
            df=df,
            sma_short=ind_cfg["sma_short"],
            sma_long=ind_cfg["sma_long"],
            rsi_period=ind_cfg["rsi_period"],
            rsi_oversold=ind_cfg["rsi_oversold"],
            rsi_overbought=ind_cfg["rsi_overbought"],
            stop_loss_pct=rules_cfg.get("stop_loss_pct", 0),
            take_profit_pct=rules_cfg.get("take_profit_pct", 0),
            purchase_price=purchase_prices.get(ticker),
        )
        all_signals.extend(signals)

    print(f"\nNájdených signálov: {len(all_signals)}\n")
    notify_signals(all_signals)


if __name__ == "__main__":
    main()
