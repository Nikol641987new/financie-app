"""Webový dashboard technických signálov pre sledované tickery."""

from html import escape
from typing import Optional

import pandas as pd
import streamlit as st
import yaml

from data_fetcher import fetch_history
from indicators import add_all_indicators
from screener import evaluate_ticker


st.set_page_config(page_title="Financie – trhové signály", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root { --ink:#17231f; --muted:#718078; --green:#137a58; --line:#e8ede9; --canvas:#f5f7f5; }
    .stApp { background:var(--canvas); color:var(--ink); }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stMainBlockContainer"] { max-width:1280px; padding:2.4rem 3.2rem 4rem; }
    [data-testid="stToolbar"], #MainMenu, footer { visibility:hidden; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
    h1, h2, h3 { font-family:'Manrope',sans-serif !important; color:var(--ink) !important; letter-spacing:-.035em; }
    h2 { font-size:1.35rem !important; font-weight:750 !important; margin:0 0 .25rem !important; }
    [data-testid="stButton"] button { border:1px solid #dce5de; border-radius:10px; background:white;
        color:var(--ink); font-weight:650; padding:.55rem 1rem; }
    [data-testid="stButton"] button:hover { border-color:var(--green); color:var(--green); }
    .topline { display:flex; align-items:center; gap:10px; color:var(--green); font-size:.72rem;
        font-weight:700; letter-spacing:.13em; text-transform:uppercase; margin-bottom:10px; }
    .topline-mark { width:9px; height:9px; border-radius:50%; background:#42a878; box-shadow:0 0 0 4px #e0f1e7; }
    .hero-title { font:800 clamp(1.8rem,3vw,2.55rem)/1.12 'Manrope',sans-serif; letter-spacing:-.055em;
        color:var(--ink); margin:0; }
    .hero-subtitle { margin:.65rem 0 0; font-size:.97rem; color:#728078; }
    .hero-rule { height:1px; background:var(--line); margin:1.65rem 0 1.35rem; }
    .metric-card { background:white; border:1px solid var(--line); border-radius:15px; padding:17px 20px; min-height:100px; }
    .metric-label { color:var(--muted); font-size:.73rem; font-weight:700; letter-spacing:.04em; }
    .metric-value { margin-top:7px; color:var(--ink); font:750 1.55rem 'Manrope',sans-serif; letter-spacing:-.04em; }
    .metric-note { margin-top:5px; color:#87928b; font-size:.73rem; }
    .section-head { margin:2rem 0 1rem; }
    .section-eyebrow { color:var(--muted); font-size:.8rem; margin-top:3px; }
    .signal-card { background:white; border:1px solid var(--line); border-radius:15px; padding:19px 20px; min-height:135px; }
    .signal-card.buy { border-top:3px solid #32966b; }
    .signal-card.sell { border-top:3px solid #d16a63; }
    .signal-title { display:flex; gap:9px; align-items:center; font:700 1rem 'Manrope',sans-serif; color:var(--ink); }
    .signal-dot { width:8px; height:8px; border-radius:50%; background:#32966b; }
    .signal-card.sell .signal-dot { background:#d16a63; }
    .signal-count { margin-left:auto; font:700 .75rem 'DM Sans',sans-serif; }
    .signal-empty { color:var(--muted); font-size:.85rem; line-height:1.55; margin-top:15px; }
    .signal-item { border-top:1px solid #eff2ef; padding-top:11px; margin-top:11px; }
    .signal-top { display:flex; justify-content:space-between; gap:12px; }
    .signal-ticker { font-weight:750; color:var(--ink); }
    .signal-price { color:var(--muted); font-size:.8rem; white-space:nowrap; }
    .signal-reason { color:#627169; font-size:.81rem; line-height:1.45; margin-top:4px; }
    .assets-list { background:white; border:1px solid var(--line); border-radius:15px; overflow:hidden; }
    .asset-row { display:grid; grid-template-columns:minmax(110px,1.15fr) minmax(125px,1.3fr) repeat(3,minmax(90px,1fr)) minmax(95px,.8fr);
        align-items:center; gap:12px; padding:14px 18px; border-bottom:1px solid #eff2ef; }
    .asset-row:last-child { border-bottom:0; }
    .asset-head { background:#fafcfb; color:#87928b; font-size:.67rem; font-weight:700; letter-spacing:.07em;
        text-transform:uppercase; padding-top:12px; padding-bottom:12px; }
    .asset-name { color:var(--ink); font-weight:750; }
    .asset-sub { color:#88938c; font-size:.74rem; margin-top:2px; }
    .asset-number { color:#35423b; font-size:.86rem; font-weight:600; }
    .badge { display:inline-flex; align-items:center; width:max-content; padding:5px 9px; border-radius:999px;
        font-size:.71rem; font-weight:700; white-space:nowrap; }
    .badge.buy { background:#eaf5ef; color:#137a58; }
    .badge.sell { background:#fbefed; color:#bd4b49; }
    .badge.mixed { background:#fff4df; color:#996913; }
    .badge.neutral { background:#f0f3f1; color:#6e7b73; }
    .asset-reason { color:#748078; font-size:.76rem; line-height:1.4; margin-top:5px; }
    .footnote { border-top:1px solid var(--line); margin-top:1.6rem; padding-top:1rem;
        color:#88938c; font-size:.74rem; line-height:1.55; }
    @media (max-width:850px) {
        [data-testid="stMainBlockContainer"] { padding:1.5rem 1.1rem 3rem; }
        .asset-row { grid-template-columns:1fr 1fr; gap:9px; padding:13px 15px; }
        .asset-head { display:none; }
        .asset-reason { grid-column:1 / -1; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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


header_left, header_right = st.columns([5, 1], vertical_alignment="center")
with header_left:
    st.markdown(
        '<div class="topline"><span class="topline-mark"></span>OSOBNÝ INVESTIČNÝ PREHĽAD</div>'
        '<div class="hero-title">Trhové signály</div>'
        '<div class="hero-subtitle">Jasný prehľad toho, čo sa deje s tvojimi sledovanými aktívami.</div>',
        unsafe_allow_html=True,
    )
with header_right:
    if st.button("↻  Obnoviť", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
st.markdown('<div class="hero-rule"></div>', unsafe_allow_html=True)

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
latest_date = max(analysis["date"] for analysis in analyses)

summary_columns = st.columns(4)
summary_items = [
    ("SLEDOVANÉ AKTÍVA", str(len(analyses)), "Akcie a ETF v zozname"),
    ("NÁKUPNÉ SIGNÁLY", str(len(buys)), "Vyžadujú tvoje posúdenie"),
    ("PREDAJNÉ SIGNÁLY", str(len(sells)), "Vyžadujú tvoje posúdenie"),
    ("POSLEDNÉ DÁTA", latest_date, "Denné dáta z Yahoo Finance"),
]
for column, (label, value, note) in zip(summary_columns, summary_items):
    with column:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">{label}</div>'
            f'<div class="metric-value">{escape(value)}</div>'
            f'<div class="metric-note">{note}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    '<div class="section-head"><h2>Čo si všímať</h2>'
    '<div class="section-eyebrow">Nové signály podľa posledných dostupných dát</div></div>',
    unsafe_allow_html=True,
)

buy_content = "".join(
    '<div class="signal-item"><div class="signal-top"><span class="signal-ticker">'
    f'{escape(analysis["ticker"])}</span><span class="signal-price">'
    f'{analysis["price"]:.2f} · {escape(analysis["date"])}</span></div>'
    '<div class="signal-reason">'
    f'{escape("; ".join(signal["reason"] for signal in analysis["signals"] if signal["type"] == "BUY"))}'
    '</div></div>'
    for analysis in buys
) or '<div class="signal-empty">Zatiaľ žiadne nové nákupné signály. Keď sa objavia, uvidíš tu aktívum aj dôvod.</div>'
sell_content = "".join(
    '<div class="signal-item"><div class="signal-top"><span class="signal-ticker">'
    f'{escape(analysis["ticker"])}</span><span class="signal-price">'
    f'{analysis["price"]:.2f} · {escape(analysis["date"])}</span></div>'
    '<div class="signal-reason">'
    f'{escape("; ".join(signal["reason"] for signal in analysis["signals"] if signal["type"] == "SELL"))}'
    '</div></div>'
    for analysis in sells
) or '<div class="signal-empty">Zatiaľ žiadne nové predajné signály. Ak nastanú, objavia sa tu aj s dôvodom.</div>'

buy_col, sell_col = st.columns(2, gap="large")
with buy_col:
    st.markdown(
        f'<div class="signal-card buy"><div class="signal-title"><span class="signal-dot"></span>'
        f'Možný nákup <span class="signal-count badge buy">{len(buys)}</span></div>{buy_content}</div>',
        unsafe_allow_html=True,
    )
with sell_col:
    st.markdown(
        f'<div class="signal-card sell"><div class="signal-title"><span class="signal-dot"></span>'
        f'Možný predaj <span class="signal-count badge sell">{len(sells)}</span></div>{sell_content}</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="section-head"><h2>Sledované aktíva</h2>'
    '<div class="section-eyebrow">Cena, technické ukazovatele a aktuálny stav</div></div>',
    unsafe_allow_html=True,
)
asset_rows = [
    '<div class="asset-row asset-head"><span>Aktívum</span><span>Aktuálny stav</span>'
    f'<span>Posledná cena</span><span>SMA {indicators_config["sma_short"]}</span>'
    f'<span>SMA {indicators_config["sma_long"]}</span><span>Dátum dát</span></div>'
]
for analysis in analyses:
    status_class = {
        "Možný nákup": "buy",
        "Možný predaj": "sell",
        "Zmiešané signály": "mixed",
        "Bez nového signálu": "neutral",
    }[analysis["status"]]
    price = f'{analysis["price"]:,.2f}'.replace(",", " ")
    short_sma = f'{analysis["sma_short"]:,.2f}'.replace(",", " ") if analysis["sma_short"] is not None else "—"
    long_sma = f'{analysis["sma_long"]:,.2f}'.replace(",", " ") if analysis["sma_long"] is not None else "—"
    reasons = "; ".join(signal["reason"] for signal in analysis["signals"]) or "Bez nového technického signálu"
    asset_rows.append(
        '<div class="asset-row">'
        f'<div><div class="asset-name">{escape(analysis["ticker"])}</div>'
        f'<div class="asset-sub">RSI {analysis["rsi"]:.1f}</div></div>'
        f'<span class="badge {status_class}">{escape(analysis["status"])}</span>'
        f'<span class="asset-number">{price}</span>'
        f'<span class="asset-number">{short_sma}</span>'
        f'<span class="asset-number">{long_sma}</span>'
        f'<span class="asset-sub">{escape(analysis["date"])}</span>'
        f'<div class="asset-reason">{escape(reasons)}</div></div>'
    )
st.markdown(f'<div class="assets-list">{"".join(asset_rows)}</div>', unsafe_allow_html=True)

st.markdown(
    '<div class="footnote">Signály vychádzajú z technických indikátorov (SMA, RSI a nastavený '
    'stop-loss/take-profit) a z posledných dostupných denných dát. Dáta sa cachujú 5 minút; '
    'tlačidlom Obnoviť ich načítaš znova. Nejde o finančné poradenstvo ani odporúčanie, '
    'koľko investovať — pred rozhodnutím zváž vlastnú situáciu a riziká. Nastavenia tickerov '
    'a pravidiel nájdeš v config.yaml.</div>',
    unsafe_allow_html=True,
)
