"""Vygeneruje statické trhové dáta, ktoré zobrazuje GitHub Pages dashboard."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yaml

from data_fetcher import fetch_history
from screener import evaluate_ticker


ROOT = Path(__file__).resolve().parent
logger = logging.getLogger(__name__)


def build_dashboard_data() -> dict:
    """Načíta konfiguráciu, vyhodnotí tickery a vráti JSON pre webovú stránku."""
    with (ROOT / "config.yaml").open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    indicators_config = config["indicators"]
    rules_config = config.get("rules", {})
    purchase_prices = config.get("purchase_prices", {}) or {}
    assets = []
    errors = []

    for ticker in config.get("tickers", []):
        try:
            prices = fetch_history(ticker, period="1y")
            latest = prices.iloc[-1]
            signals = evaluate_ticker(
                ticker=ticker,
                df=prices,
                sma_short=indicators_config["sma_short"],
                sma_long=indicators_config["sma_long"],
                rsi_period=indicators_config["rsi_period"],
                rsi_oversold=indicators_config["rsi_oversold"],
                rsi_overbought=indicators_config["rsi_overbought"],
                stop_loss_pct=rules_config.get("stop_loss_pct", 0),
                take_profit_pct=rules_config.get("take_profit_pct", 0),
                purchase_price=purchase_prices.get(ticker),
            )
            signal_types = {signal.signal_type for signal in signals}
            if signal_types == {"BUY", "SELL"}:
                status = "Zmiešané signály"
            elif "BUY" in signal_types:
                status = "Možný nákup"
            elif "SELL" in signal_types:
                status = "Možný predaj"
            else:
                status = "Bez nového signálu"

            assets.append(
                {
                    "ticker": ticker,
                    "date": pd.Timestamp(prices.index[-1]).strftime("%d.%m.%Y"),
                    "price": float(latest["Close"]),
                    "sma_short": (
                        float(prices["Close"].rolling(indicators_config["sma_short"]).mean().iloc[-1])
                        if len(prices) >= indicators_config["sma_short"]
                        else None
                    ),
                    "sma_long": (
                        float(prices["Close"].rolling(indicators_config["sma_long"]).mean().iloc[-1])
                        if len(prices) >= indicators_config["sma_long"]
                        else None
                    ),
                    "rsi": _latest_rsi(prices["Close"], indicators_config["rsi_period"]),
                    "status": status,
                    "signals": [
                        {"type": signal.signal_type, "reason": signal.reason}
                        for signal in signals
                    ],
                }
            )
        except Exception as error:
            logger.exception("Nepodarilo sa spracovať ticker %s", ticker)
            errors.append({"ticker": ticker, "message": str(error)})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sma_short_period": indicators_config["sma_short"],
        "sma_long_period": indicators_config["sma_long"],
        "assets": assets,
        "errors": errors,
    }


def _latest_rsi(close: pd.Series, period: int) -> float | None:
    """Vypočíta posledné RSI rovnakým spôsobom ako hlavný screener."""
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0.0).rolling(window=period).mean()
    relative_strength = gain / loss
    latest_rsi = 100 - (100 / (1 + relative_strength))
    value = latest_rsi.iloc[-1]
    return float(value) if pd.notna(value) else None


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    output_path = ROOT / "site" / "data.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = build_dashboard_data()
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info(
        "Dashboard dáta uložené do %s (%d aktív, %d chýb)",
        output_path,
        len(data["assets"]),
        len(data["errors"]),
    )
    if not data["assets"]:
        raise RuntimeError("Nepodarilo sa načítať dáta pre žiadny ticker.")


if __name__ == "__main__":
    main()
