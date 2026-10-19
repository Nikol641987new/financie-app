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

Stránka je dostupná priamo cez GitHub Pages:

https://nikol641987new.github.io/financie-app/

Statický web používa trhové údaje, ktoré vytvorí GitHub Actions. Údaje sa
obnovujú pri každom pushi do `main`, manuálnom spustení workflow a automaticky
v pracovné dni o 22:15 UTC. Ak GitHub Pages ešte nie je prepojené s workflow,
v repozitári otvor **Settings → Pages** a nastav **Source: GitHub Actions**.
Stav nasadenia nájdeš v **Actions → Build and deploy dashboard**.

Stránku môžeš spustiť aj lokálne v interaktívnej Streamlit verzii:

```bash
streamlit run app.py
```

Obe verzie používajú tickery a pravidlá z `config.yaml`. GitHub Pages prevádza
USD ceny na EUR podľa najnovšieho dostupného kurzu `EURUSD=X` z Yahoo Finance;
natívne eurové ceny zostávajú bez prepočtu. Tlačidlo **Obnoviť** načíta
naposledy publikované dáta; nové ceny a kurz sa získajú pri ďalšom úspešnom
spustení workflow. Lokálna Streamlit verzia zobrazuje natívne ceny trhu.

Signály sú iba technické indikácie založené na minulých cenách, nie finančné
poradenstvo ani záruka budúceho vývoja.

### Krátkodobý prehľad

Webový prehľad zoraďuje tickery z `screening_tickers` do kategórií „Možný
vstup“, „Vyčkať“ a „Slabý trend“. Možný vstup vyžaduje cenu nad SMA 50, SMA 50
nad SMA 200, kladný 3- aj 6-mesačný výnos a RSI v pásme 45–65. Slabý trend
znamená cenu pod oboma priemermi a záporný 3-mesačný výnos. Ostatné prípady
zostávajú v kategórii „Vyčkať“. Ide o jednoduchý filter historických údajov,
nie predpoveď ani automatický pokyn na kúpu alebo predaj.

Na stránke môžeš zvoliť orientačný rozpočet 10 €, 20 €, 50 € alebo zadať
vlastnú sumu; prepočet na zlomok akcie nezohľadňuje poplatky a závisí od
podpory brokera. Prehľad sa obnoví po úspešnom spustení GitHub Actions.

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

Workflow `.github/workflows/deploy-pages.yml` automaticky vytvára web pre
GitHub Pages a obnovuje jeho trhové dáta v pracovné dni o 22:15 UTC.

Ak chceš používať Telegram notifikácie, pridaj údaje ako **GitHub Secrets**:

1. V repozitári choď na **Settings → Secrets and variables → Actions**
2. Klikni **New repository secret** a pridaj:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. Telegram notifikácie sa spúšťajú samostatne príkazom `python main.py`.
   Workflow GitHub Pages aktualizuje web a trhové dáta.

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
├── build_dashboard_data.py  # generovanie JSON s trhovými dátami
├── site/                    # statická stránka pre GitHub Pages
└── .github/workflows/
    └── deploy-pages.yml     # nasadenie stránky a obnova dát
```

## Možné rozšírenia

- Pridať MACD, Bollingerove pásma (`indicators.py`)
- Pridať screener na väčší zoznam akcií (napr. celý S&P 500)
- Napojiť AI vrstvu (Claude API) na zhrnutie/vysvetlenie signálov
- Backtesting modul na otestovanie stratégie na historických dátach
  pred nasadením naostro
