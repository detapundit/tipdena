# 🇮🇳 Indian Stock Advisor

AI-powered stock recommendation engine for NSE/BSE listed stocks.
Uses **Claude (Anthropic)** for intelligent analysis and **Valkey** for fast caching.

---

## Architecture

```
NSE/BSE Data (yfinance + nsepython)
        │
        ▼
Valkey Cache (prices, history, fundamentals, news)
        │
        ├── Fundamental Engine ──► Score & Filter ──► Claude AI ──► Top 3 per Cap
        │   (P/E, ROE, Growth,                         (Long-term picks)
        │    Margins, D/E, CR)
        │
        └── Technical Engine ──► Compute Indicators ──► Claude AI ──► Top 3 per Cap
            (RSI, MACD, EMA,                             (Short-term trades)
             ADX, BB, Stoch,
             ATR, Volume)
                │
                ▼
          Console Output
```

---

## Setup

### 1. Install Valkey

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install -y valkey
valkey-server --daemonize yes

# macOS
brew install valkey
valkey-server --daemonize yes

# Docker (easiest)
docker run -d -p 6379:6379 --name valkey valkey/valkey:latest
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your Anthropic API Key

Edit `config.py`:
```python
ANTHROPIC_API_KEY = "sk-ant-..."   # Your Claude API key
```

Or set as environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Usage

```bash
# Full analysis (fundamental + technical) — takes ~5 min on first run
python main.py

# Technical analysis only (faster ~2 min)
python main.py --tech-only

# Fundamental analysis only
python main.py --fund-only

# Clear all cache and re-fetch everything
python main.py --clear-cache

# Analyse specific stocks only
python main.py --stocks RELIANCE.NS TCS.NS INFY.NS HDFCBANK.NS
```

---

## Output Format

```
══════════════════════════════════════════════════════
  FUNDAMENTAL ANALYSIS — LONG-TERM PICKS (1–3 Years)
══════════════════════════════════════════════════════

  🔵 LARGE CAP FUNDAMENTAL PICKS
  ─────────────────────────────
  #1  TCS.NS  —  Tata Consultancy Services
  Sector: Technology   |   Horizon: 12-18 months
  Current Price   :  ₹3,845.00
  Entry Zone      :  ₹3,700.00  –  ₹3,850.00
  Target Zone     :  ₹4,500.00  –  ₹5,000.00
  Expected Return :  22.5%

  Investment Thesis:
  TCS shows consistent revenue growth with industry-leading margins...

══════════════════════════════════════════════════════
  TECHNICAL ANALYSIS — SHORT-TO-MEDIUM TERM TRADES
══════════════════════════════════════════════════════

  #1  RELIANCE.NS  —  Reliance Industries
  Setup: EMA Golden Cross + RSI Reversal
  Entry Zone   :  ₹2,850  –  ₹2,900
  Target Zone  :  ₹3,100  –  ₹3,250
  Stop Loss    :  ₹2,780
```

---

## Data Sources

| Source | Data | Refresh |
|--------|------|---------|
| `yfinance` | Prices, OHLCV, Fundamentals | 5 min (prices), 1h (history), 24h (fundamentals) |
| Google News RSS | Market & stock news | 30 min |
| Yahoo Finance News | Stock-specific news | 30 min |

---

## Valkey Cache Keys

| Key Pattern | Content | TTL |
|-------------|---------|-----|
| `price:<ticker>` | Latest price data | 5 min |
| `history:<ticker>` | 1-year OHLCV DataFrame | 1 hour |
| `fundamentals:<ticker>` | P/E, ROE, margins, growth | 24 hours |
| `news:<ticker>` | Stock news headlines | 30 min |
| `market:news` | Broad market news | 30 min |
| `tech_score:<ticker>` | Computed indicator scores | 1 hour |
| `recommendations:fundamental` | Final AI fund recs | session |
| `recommendations:technical` | Final AI tech recs | session |

---

## File Structure

```
stock_advisor/
├── config.py         ← All settings, stock lists, thresholds
├── db.py             ← Valkey cache layer
├── data_fetcher.py   ← Prices, OHLCV, fundamentals, news
├── fundamental.py    ← Fundamental scoring & filtering
├── technical.py      ← Technical indicator computation & scoring
├── ai_analyzer.py    ← Claude API integration & prompts
├── reporter.py       ← Console output formatter
├── main.py           ← Main orchestrator
└── requirements.txt
```

---

## Disclaimer

> ⚠ This tool is for **educational and research purposes only**.
> It does not constitute SEBI-registered investment advice.
> Always consult a qualified financial advisor before investing.
