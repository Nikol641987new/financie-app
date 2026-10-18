"""Webový dashboard technických signálov pre sledované tickery."""

from typing import Optional

import pandas as pd
import streamlit as st
import yaml

from data_fetcher import fetch_history
from indicators import add_all_indicators
from screener import evaluate_ticker


st.set_page_config(page_title="Financie – trhové signály", page_icon="📈", layout="wide")


@st.cache_data(ttl=300, show_spinner=False)
def analyze_ticker(
    ticker: str,
    sma_short: int,
    sma_long: int,
    rsi_period: int,
    rsi_oversold: float,
    rsi_overbought: float,
    stop_loss_pct: float,
    take_profit_pct: float,
    purchase_price: Optional[float],
) -> dict:
    """Načíta posledné dáta a vyhodnotí ticker podľa pravidiel screenera."""
    prices = fetch_history(ticker, period="1y")
    indicators = add_all_indicators(prices, sma_short, sma_long, rsi_period)
    latest = indicators.iloc[-1]

    signals = evaluate_ticker(
        ticker=ticker,
        df=prices,
        sma_short=sma_short,
        sma_long=sma_long,
        rsi_period=rsi_period,
        rsi_oversold=rsi_oversold,
        rsi_overbought=rsi_overbought,
        stop_loss_pct=stop_loss_pct,
        take_profit_pct=take_profit_pct,
        purchase_price=purchase_price,
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

    last_date = pd.Timestamp(indicators.index[-1]).strftime("%d.%m.%Y")
    return {
        "ticker": ticker,
        "date": last_date,
        "price": float(latest["Close"]),
        "sma_short": float(latest["SMA_short"]) if pd.notna(latest["SMA_short"]) else None,
        "sma_long": float(latest["SMA_long"]) if pd.notna(latest["SMA_long"]) else None,
        "rsi": float(latest["RSI"]) if pd.notna(latest["RSI"]) else None,
        "status": status,
        "signals": [
            {"type": signal.signal_type, "reason": signal.reason, "price": signal.price}
            for signal in signals
        ],
    }


def load_config() -> dict:
    """Načíta nastavenia z config.yaml."""
    with open("config.yaml", "r", encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


st.title("📈 Financie – prehľad trhových signálov")
st.caption(
    "Sledujte, pri ktorých aktívach nastal technický nákupný alebo predajný signál. "
    "Dáta sa cachujú na 5 minút; na okamžité načítanie použite tlačidlo Obnoviť dáta."
)

try:
    config = load_config()
except (OSError, yaml.YAMLError) as error:
    st.error(f"Nepodarilo sa načítať config.yaml: {error}")
    st.stop()

tickers = config.get("tickers", [])
indicators_config = config.get("indicators", {})
rules_config = config.get("rules", {})
purchase_prices = config.get("purchase_prices", {}) or {}

if not tickers:
    st.warning("V config.yaml nie sú nastavené žiadne sledované tickery.")
    st.stop()

required_indicator_settings = ("sma_short", "sma_long", "rsi_period", "rsi_oversold", "rsi_overbought")
missing_settings = [key for key in required_indicator_settings if key not in indicators_config]
if missing_settings:
    st.error(f"V config.yaml chýbajú nastavenia indikátorov: {', '.join(missing_settings)}")
    st.stop()

if st.button("Obnoviť dáta", type="primary"):
    st.cache_data.clear()
    st.rerun()

analyses = []
errors = []
with st.spinner("Načítavam trhové dáta a počítam signály..."):
    for ticker in tickers:
        try:
            analyses.append(
                analyze_ticker(
                    ticker=ticker,
                    sma_short=indicators_config["sma_short"],
                    sma_long=indicators_config["sma_long"],
                    rsi_period=indicators_config["rsi_period"],
                    rsi_oversold=indicators_config["rsi_oversold"],
                    rsi_overbought=indicators_config["rsi_overbought"],
                    stop_loss_pct=rules_config.get("stop_loss_pct", 0),
                    take_profit_pct=rules_config.get("take_profit_pct", 0),
                    purchase_price=purchase_prices.get(ticker),
                )
            )
        except Exception as error:
            errors.append((ticker, str(error)))

if errors:
    for ticker, error in errors:
        st.error(f"{ticker}: nepodarilo sa načítať alebo vyhodnotiť dáta ({error})")

if not analyses:
    st.warning("Pre žiadny ticker sa nepodarilo načítať údaje. Skontrolujte pripojenie a názvy tickerov.")
    st.stop()

buys = [analysis for analysis in analyses if any(signal["type"] == "BUY" for signal in analysis["signals"])]
sells = [analysis for analysis in analyses if any(signal["type"] == "SELL" for signal in analysis["signals"])]
buy_col, sell_col = st.columns(2)

with buy_col:
    st.subheader("Možné nákupné príležitosti")
    if not buys:
        st.info("V posledných dostupných dátach nebol zistený nový nákupný signál.")
    for analysis in buys:
        reasons = [signal["reason"] for signal in analysis["signals"] if signal["type"] == "BUY"]
        st.success(f"**{analysis['ticker']}** · {analysis['price']:.2f} · dáta k {analysis['date']}")
        for reason in reasons:
            st.write(f"- {reason}")

with sell_col:
    st.subheader("Možné predaje")
    if not sells:
        st.info("V posledných dostupných dátach nebol zistený nový predajný signál.")
    for analysis in sells:
        reasons = [signal["reason"] for signal in analysis["signals"] if signal["type"] == "SELL"]
        st.warning(f"**{analysis['ticker']}** · {analysis['price']:.2f} · dáta k {analysis['date']}")
        for reason in reasons:
            st.write(f"- {reason}")

st.subheader("Všetky sledované aktíva")
table_rows = []
for analysis in analyses:
    table_rows.append(
        {
            "Ticker": analysis["ticker"],
            "Signál": analysis["status"],
            "Cena": analysis["price"],
            f"SMA {indicators_config['sma_short']}": analysis["sma_short"],
            f"SMA {indicators_config['sma_long']}": analysis["sma_long"],
            "RSI": analysis["rsi"],
            "Dátum dát": analysis["date"],
            "Dôvody": "; ".join(signal["reason"] for signal in analysis["signals"]) or "—",
        }
    )
st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

st.caption(
    "Signály vychádzajú len z technických indikátorov (SMA, RSI a nastavený stop-loss/take-profit) "
    "a z posledných dostupných denných dát. Zoznam tickerov nastavíte v config.yaml. "
    "Nejde o finančné poradenstvo; pred investovaním si overte aj vlastnú situáciu a riziká."
)
