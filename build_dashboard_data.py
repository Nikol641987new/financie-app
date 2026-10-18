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
    watched_tickers = list(dict.fromkeys(config.get("tickers", [])))
    screening_tickers = list(dict.fromkeys(config.get("screening_tickers", watched_tickers)))
    data_tickers = list(dict.fromkeys(watched_tickers + screening_tickers))
    default_currency = config.get("default_currency", "USD")
    currency_overrides = config.get("currencies", {})
    currencies = {
        ticker: currency_overrides.get(ticker, default_currency)
        for ticker in data_tickers
    }
    usd_to_eur = None
    fx_date = None
    if "USD" in currencies.values():
        fx_history = fetch_history("EURUSD=X", period="5d")
        usd_per_eur = float(fx_history["Close"].iloc[-1])
        if usd_per_eur <= 0:
            raise ValueError(f"Neplatný kurz USD/EUR z Yahoo Finance: {usd_per_eur}")
        usd_to_eur = 1 / usd_per_eur
        fx_date = pd.Timestamp(fx_history.index[-1]).strftime("%d.%m.%Y")

    assets = []
    candidates = []
    errors = []

    for ticker in data_tickers:
        try:
            prices = fetch_history(ticker, period="2y")
            latest = prices.iloc[-1]
            currency = currencies[ticker]
            if currency == "EUR":
                conversion_to_eur = 1.0
            elif currency == "USD":
                conversion_to_eur = usd_to_eur
            else:
                raise ValueError(
                    f"Mena {currency} pre {ticker} nie je podporovaná. "
                    "Zatiaľ sú podporované USD a EUR."
                )

            sma_short = (
                float(prices["Close"].rolling(indicators_config["sma_short"]).mean().iloc[-1])
                if len(prices) >= indicators_config["sma_short"]
                else None
            )
            sma_long = (
                float(prices["Close"].rolling(indicators_config["sma_long"]).mean().iloc[-1])
                if len(prices) >= indicators_config["sma_long"]
                else None
            )
            signals = []
            if ticker in watched_tickers:
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

            asset = {
                "ticker": ticker,
                "date": pd.Timestamp(prices.index[-1]).strftime("%d.%m.%Y"),
                "price_currency": "EUR",
                "price": float(latest["Close"]) * conversion_to_eur,
                "sma_short": sma_short * conversion_to_eur if sma_short is not None else None,
                "sma_long": sma_long * conversion_to_eur if sma_long is not None else None,
                "rsi": _latest_rsi(prices["Close"], indicators_config["rsi_period"]),
                "status": status,
                "signals": [
                    {
                        "type": signal.signal_type,
                        "reason": _display_reason(
                            reason=signal.reason,
                            currency=currency,
                            current_price=float(latest["Close"]),
                            purchase_price=purchase_prices.get(ticker),
                            conversion_to_eur=conversion_to_eur,
                        ),
                    }
                    for signal in signals
                ],
            }

            if ticker in watched_tickers:
                assets.append(asset)
            if ticker in screening_tickers:
                trend = _growth_trend(
                    prices["Close"],
                    sma_short=sma_short,
                    sma_long=sma_long,
                    price=float(latest["Close"]),
                    conversion_to_eur=conversion_to_eur,
                    asset_date=asset["date"],
                )
                if trend is not None:
                    candidates.append({"ticker": ticker, "price": asset["price"], **trend})
        except Exception as error:
            logger.exception("Nepodarilo sa spracovať ticker %s", ticker)
            errors.append({"ticker": ticker, "message": str(error)})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sma_short_period": indicators_config["sma_short"],
        "sma_long_period": indicators_config["sma_long"],
        "currency": "EUR",
        "usd_to_eur": usd_to_eur,
        "fx_date": fx_date,
        "assets": assets,
        "screened_tickers": len(screening_tickers),
        "candidates": sorted(
            candidates,
            key=lambda candidate: (candidate["momentum_3_12m_pct"], candidate["return_6m_pct"]),
            reverse=True,
        ),
        "errors": errors,
    }


def _growth_trend(
    close: pd.Series,
    sma_short: float | None,
    sma_long: float | None,
    price: float,
    conversion_to_eur: float,
    asset_date: str,
) -> dict | None:
    """Vyberie rastový trend len pri potvrdení ceny, priemerov a 3–6m výnosov."""
    if len(close) < 253 or sma_short is None or sma_long is None:
        return None

    return_3m = (float(close.iloc[-1]) / float(close.iloc[-64]) - 1) * 100
    return_6m = (float(close.iloc[-1]) / float(close.iloc[-127]) - 1) * 100
    return_12m = (float(close.iloc[-1]) / float(close.iloc[-253]) - 1) * 100

    # Filter on raw market-currency data, before applying the display FX rate.
    latest_price = float(close.iloc[-1])
    short_sma_market = sma_short / conversion_to_eur
    long_sma_market = sma_long / conversion_to_eur
    if not (
        latest_price > short_sma_market > long_sma_market
        and return_3m > 0
        and return_6m > 0
    ):
        return None

    momentum_3_12m = return_3m * 0.4 + return_6m * 0.35 + return_12m * 0.25
    return {
        "date": asset_date,
        "return_3m_pct": return_3m,
        "return_6m_pct": return_6m,
        "return_12m_pct": return_12m,
        "momentum_3_12m_pct": momentum_3_12m,
    }


def _display_reason(
    reason: str,
    currency: str,
    current_price: float,
    purchase_price: float | None,
    conversion_to_eur: float,
) -> str:
    """Zobrazí stop-loss/take-profit nákupnú cenu aj v EUR."""
    if purchase_price is None or purchase_price <= 0:
        return reason

    change_pct = (current_price - purchase_price) / purchase_price * 100
    if currency not in {"USD", "EUR"}:
        return reason
    purchase_price_eur = purchase_price * conversion_to_eur
    if reason.startswith("Stop-loss:"):
        return (
            f"Stop-loss: cena klesla o {change_pct:.1f}% od nákupnej ceny "
            f"{purchase_price_eur:.2f} €"
        )
    if reason.startswith("Take-profit:"):
        return (
            f"Take-profit: zisk {change_pct:.1f}% od nákupnej ceny "
            f"{purchase_price_eur:.2f} €"
        )
    return reason


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
