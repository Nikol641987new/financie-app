# Stock Notifier

Jednoduchý nástroj, ktorý sleduje zadané akcie/ETF a posiela notifikácie
(cez Telegram), keď nastane technický signál na nákup alebo predaj
(Golden/Death Cross, RSI prekúpenosť/prepredanosť, stop-loss, take-profit).

⚠️ **Upozornenie:** Toto nie je finančné poradenstvo. Signály sú založené
na jednoduchých technických indikátoroch z minulých dát a nezaručujú
budúci vývoj ceny. Finálne rozhodnutie o nákupe/predaji je vždy na tebe.

## Čo appka robí

1. Stiahne historické ceny pre tickery zo `config.yaml` (cez Yahoo Finance)
2. Spočíta indikátory: SMA 50/200, RSI
3. Vyhodnotí pravidlá (Golden/Death Cross, RSI hranice, stop-loss/take-profit)
4. Pošle výsledok cez Telegram bota (alebo vypíše do konzoly)

## 1. Lokálne spustenie

```bash
pip install -r requirements.txt
python main.py
```

## Webový prehľad signálov

Na zobrazenie sledovaných aktív, cien a nákupných/predajných signálov spusti:

```bash
streamlit run app.py
```

Stránka ukazuje signály vypočítané z posledných dostupných denných dát a pravidiel
v `config.yaml`. Načítané dáta sa cachujú na 5 minút; tlačidlom **Obnoviť dáta**
ich možno načítať aj manuálne. Zoznam sledovaných tickerov a indikátory upravíš
v `config.yaml`.

Signály sú iba technické indikácie založené na minulých cenách, nie finančné
poradenstvo ani záruka budúceho vývoja.

## 2. Nastavenie tickerov a pravidiel

Uprav `config.yaml` — pridaj/uber tickery, uprav prahové hodnoty RSI,
stop-loss %, take-profit %, prípadne nákupné ceny pre stop-loss výpočty.

## 3. Nastavenie Telegram notifikácií

1. V Telegrame napíš **@BotFather** → príkaz `/newbot` → over meno,
   dostaneš **bot token** (napr. `123456:ABC-DEF...`)
2. Napíš svojmu novému botovi akúkoľvek správu (aby ťa "poznal")
3. Otvor v prehliadači:
   `https://api.telegram.org/bot<TVOJ_TOKEN>/getUpdates`
   a nájdi svoje **chat_id** v JSON odpovedi (`"chat":{"id": ...}`)
4. Nastav premenné prostredia lokálne:
   ```bash
   export TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
   export TELEGRAM_CHAT_ID="123456789"
   ```

## 4. Automatické spúšťanie cez GitHub Actions (zadarmo)

Repozitár už obsahuje workflow `.github/workflows/daily-screener.yml`,
ktorý beží automaticky každý pracovný deň o 18:00 UTC.

Aby fungoval, treba pridať Telegram údaje ako **GitHub Secrets**:

1. V repozitári choď na **Settings → Secrets and variables → Actions**
2. Klikni **New repository secret** a pridaj:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Workflow sa spustí automaticky podľa plánu, alebo ho vieš spustiť
   manuálne cez záložku **Actions → Daily Stock Screener → Run workflow**

## Štruktúra projektu

```
stock-notifier/
├── config.yaml          # tickery, pravidlá, prahové hodnoty
├── data_fetcher.py       # sťahovanie cien (yfinance)
├── indicators.py         # SMA, RSI výpočty
├── screener.py           # logika signálov BUY/SELL
├── notifier.py            # Telegram notifikácie
├── main.py                # hlavný orchestračný skript
├── requirements.txt
└── .github/workflows/
    └── daily-screener.yml  # automatické denné spúšťanie
```

## Možné rozšírenia

- Pridať MACD, Bollingerove pásma (`indicators.py`)
- Pridať screener na väčší zoznam akcií (napr. celý S&P 500)
- Napojiť AI vrstvu (Claude API) na zhrnutie/vysvetlenie signálov
- Backtesting modul na otestovanie stratégie na historických dátach
  pred nasadením naostro
