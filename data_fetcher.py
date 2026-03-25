"""
data_fetcher.py - Fetches prices, history, fundamentals, news for Indian stocks
Sources: yfinance (primary), NSE/BSE unofficial, Google/Moneycontrol news
"""

import time
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

import db
from config import (
    ALL_STOCKS, LARGE_CAP_STOCKS, MID_CAP_STOCKS, SMALL_CAP_STOCKS,
    HISTORY_PERIOD, HISTORY_INTERVAL,
    TTL_PRICE, TTL_HISTORY, TTL_FUNDAMENTALS, TTL_NEWS,
    MIN_PRICE, MIN_VOLUME, MIN_MARKET_CAP,
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


# ─────────────────────────────────────────────
# 1. Live Price
# ─────────────────────────────────────────────
def fetch_price(ticker: str) -> dict | None:
    """Fetch latest price for a single ticker, with Valkey cache."""
    cached = db.load_price(ticker)
    if cached:
        return cached

    try:
        tk = yf.Ticker(ticker)
        info = tk.fast_info          # lightweight – just price data
        price = {
            "ticker"       : ticker,
            "last_price"   : round(float(info.last_price or 0), 2),
            "prev_close"   : round(float(info.previous_close or 0), 2),
            "day_high"     : round(float(info.day_high or 0), 2),
            "day_low"      : round(float(info.day_low or 0), 2),
            "volume"       : int(info.three_month_average_volume or 0),
            "market_cap"   : float(info.market_cap or 0),
            "fetched_at"   : datetime.now().isoformat(),
        }
        if price["last_price"] > 0:
            db.save_price(ticker, price, TTL_PRICE)
            return price
    except Exception as e:
        pass   # silently skip; caller handles None
    return None


def fetch_all_prices(stocks: list = None) -> dict:
    """Fetch prices for all stocks in batch. Returns {ticker: price_dict}."""
    stocks = stocks or ALL_STOCKS
    results = {}
    print(f"\n  [Prices] Fetching prices for {len(stocks)} stocks …")

    # yfinance supports batch download
    tickers_str = " ".join(stocks)
    try:
        data = yf.download(
            tickers_str,
            period="2d",
            interval="1d",
            group_by="ticker",
            auto_adjust=True,
            progress=False,
            threads=True,
        )
    except Exception as e:
        print(f"  [Prices] Batch download failed: {e}")
        data = None

    for ticker in stocks:
        cached = db.load_price(ticker)
        if cached:
            results[ticker] = cached
            continue

        try:
            if data is not None and len(stocks) > 1:
                row = data[ticker].dropna().iloc[-1] if ticker in data.columns.get_level_values(0) else None
            else:
                row = None

            if row is not None:
                price = {
                    "ticker"     : ticker,
                    "last_price" : round(float(row["Close"]), 2),
                    "day_high"   : round(float(row["High"]), 2),
                    "day_low"    : round(float(row["Low"]), 2),
                    "volume"     : int(row["Volume"]),
                    "prev_close" : round(float(row["Open"]), 2),
                    "market_cap" : 0,
                    "fetched_at" : datetime.now().isoformat(),
                }
                db.save_price(ticker, price, TTL_PRICE)
                results[ticker] = price
            else:
                p = fetch_price(ticker)
                if p:
                    results[ticker] = p
        except Exception:
            p = fetch_price(ticker)
            if p:
                results[ticker] = p

        time.sleep(0.05)   # gentle rate limiting

    print(f"  [Prices] Retrieved {len(results)}/{len(stocks)} prices")
    return results


# ─────────────────────────────────────────────
# 2. OHLCV History
# ─────────────────────────────────────────────
def fetch_history(ticker: str) -> pd.DataFrame | None:
    """Fetch 1-year daily OHLCV. Cached in Valkey."""
    cached = db.load_history(ticker)
    if cached is not None and not cached.empty:
        return cached

    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period=HISTORY_PERIOD, interval=HISTORY_INTERVAL, auto_adjust=True)
        if df is not None and len(df) > 50:
            df.index = pd.to_datetime(df.index)
            db.save_history(ticker, df, TTL_HISTORY)
            return df
    except Exception as e:
        pass
    return None


# ─────────────────────────────────────────────
# 3. Fundamentals
# ─────────────────────────────────────────────
def fetch_fundamentals(ticker: str) -> dict | None:
    """Fetch fundamental data. Cached for 24h."""
    cached = db.load_fundamentals(ticker)
    if cached:
        return cached

    try:
        tk = yf.Ticker(ticker)
        info = tk.info

        def safe(key, default=None):
            val = info.get(key, default)
            return val if val not in (None, "None", "") else default

        # Revenue growth: compare ttm vs prior year
        rev_growth = None
        try:
            fin = tk.financials
            if fin is not None and not fin.empty and fin.shape[1] >= 2:
                rev_now  = fin.loc["Total Revenue"].iloc[0]
                rev_prev = fin.loc["Total Revenue"].iloc[1]
                rev_growth = round(((rev_now - rev_prev) / abs(rev_prev)) * 100, 2) if rev_prev else None
        except Exception:
            pass

        # Earnings growth
        earn_growth = None
        try:
            fin = tk.financials
            if fin is not None and not fin.empty and fin.shape[1] >= 2:
                e_now  = fin.loc["Net Income"].iloc[0]
                e_prev = fin.loc["Net Income"].iloc[1]
                earn_growth = round(((e_now - e_prev) / abs(e_prev)) * 100, 2) if e_prev else None
        except Exception:
            pass

        pe    = safe("trailingPE")
        eps   = safe("trailingEps")
        peg   = safe("pegRatio")
        pb    = safe("priceToBook")
        roe   = safe("returnOnEquity")
        roa   = safe("returnOnAssets")
        de    = safe("debtToEquity")
        cr    = safe("currentRatio")
        pm    = safe("profitMargins")
        om    = safe("operatingMargins")
        mcap  = safe("marketCap")
        sector= safe("sector", "Unknown")
        ind   = safe("industry", "Unknown")

        fund = {
            "ticker"           : ticker,
            "company_name"     : safe("longName", ticker),
            "sector"           : sector,
            "industry"         : ind,
            "market_cap_cr"    : round(mcap / 1e7, 2) if mcap else None,  # ₹ Crore
            "pe_ratio"         : round(float(pe), 2) if pe else None,
            "peg_ratio"        : round(float(peg), 2) if peg else None,
            "pb_ratio"         : round(float(pb), 2) if pb else None,
            "eps"              : round(float(eps), 2) if eps else None,
            "roe_pct"          : round(float(roe) * 100, 2) if roe else None,
            "roa_pct"          : round(float(roa) * 100, 2) if roa else None,
            "debt_equity"      : round(float(de) / 100, 2) if de else None,  # yf returns as %
            "current_ratio"    : round(float(cr), 2) if cr else None,
            "profit_margin_pct": round(float(pm) * 100, 2) if pm else None,
            "operating_margin_pct": round(float(om) * 100, 2) if om else None,
            "revenue_growth_pct": rev_growth,
            "earnings_growth_pct": earn_growth,
            "52w_high"         : safe("fiftyTwoWeekHigh"),
            "52w_low"          : safe("fiftyTwoWeekLow"),
            "avg_volume"       : safe("averageVolume"),
            "dividend_yield"   : round(float(safe("dividendYield", 0)) * 100, 2),
            "beta"             : safe("beta"),
            "fetched_at"       : datetime.now().isoformat(),
        }

        db.save_fundamentals(ticker, fund, TTL_FUNDAMENTALS)
        return fund

    except Exception as e:
        return None


def fetch_all_fundamentals(stocks: list = None) -> dict:
    """Fetch fundamentals for all stocks. Returns {ticker: fund_dict}."""
    stocks = stocks or ALL_STOCKS
    results = {}
    print(f"\n  [Fundamentals] Fetching for {len(stocks)} stocks (may take 2-3 min) …")
    for i, ticker in enumerate(stocks, 1):
        fund = fetch_fundamentals(ticker)
        if fund:
            results[ticker] = fund
        if i % 10 == 0:
            print(f"  [Fundamentals] {i}/{len(stocks)} done …")
        time.sleep(0.3)   # respect rate limits
    print(f"  [Fundamentals] Retrieved {len(results)}/{len(stocks)}")
    return results


# ─────────────────────────────────────────────
# 4. News Feed
# ─────────────────────────────────────────────
def fetch_google_news(query: str, max_items: int = 5) -> list:
    """Scrape Google News RSS for a stock or market query."""
    url = f"https://news.google.com/rss/search?q={requests.utils.quote(query)}+NSE+stock&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(resp.content, "lxml-xml")
        items = []
        for item in soup.find_all("item")[:max_items]:
            items.append({
                "title"     : item.title.text if item.title else "",
                "link"      : item.link.text if item.link else "",
                "published" : item.pubDate.text if item.pubDate else "",
                "source"    : item.source.text if item.source else "Google News",
            })
        return items
    except Exception:
        return []


def fetch_stock_news(ticker: str) -> list:
    """Get news for a specific ticker. Cached 30 min."""
    cached = db.load_news(ticker)
    if cached:
        return cached

    # Try yfinance news first
    articles = []
    try:
        tk = yf.Ticker(ticker)
        yf_news = tk.news or []
        for n in yf_news[:5]:
            articles.append({
                "title"    : n.get("content", {}).get("title", ""),
                "link"     : n.get("content", {}).get("canonicalUrl", {}).get("url", ""),
                "published": n.get("content", {}).get("pubDate", ""),
                "source"   : n.get("content", {}).get("provider", {}).get("displayName", "Yahoo Finance"),
            })
    except Exception:
        pass

    # Supplement with Google News
    symbol = ticker.replace(".NS", "").replace(".BO", "")
    google_news = fetch_google_news(symbol)
    articles.extend(google_news)

    # Deduplicate by title
    seen, unique = set(), []
    for a in articles:
        if a["title"] and a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    db.save_news(ticker, unique[:8], TTL_NEWS)
    return unique[:8]


def fetch_market_news() -> list:
    """Fetch broad Indian market news."""
    cached = db.load_market_news()
    if cached:
        return cached

    articles = []
    queries = ["NSE India stock market", "BSE Sensex Nifty", "Indian stock market today"]
    for q in queries:
        articles.extend(fetch_google_news(q, max_items=4))
        time.sleep(0.5)

    seen, unique = set(), []
    for a in articles:
        if a["title"] and a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)

    db.save_market_news(unique[:15], TTL_NEWS)
    return unique[:15]


# ─────────────────────────────────────────────
# 5. Cap classifier
# ─────────────────────────────────────────────
def classify_cap(ticker: str, market_cap_cr: float = None) -> str:
    """Return 'Large', 'Mid', or 'Small' for a ticker."""
    if ticker in LARGE_CAP_STOCKS:
        return "Large"
    if ticker in MID_CAP_STOCKS:
        return "Mid"
    if ticker in SMALL_CAP_STOCKS:
        return "Small"
    # Fallback to market cap
    from config import LARGE_CAP_MIN, MID_CAP_MIN, SMALL_CAP_MIN
    if market_cap_cr:
        if market_cap_cr >= LARGE_CAP_MIN:
            return "Large"
        if market_cap_cr >= MID_CAP_MIN:
            return "Mid"
        if market_cap_cr >= SMALL_CAP_MIN:
            return "Small"
    return "Unknown"


def get_sector(ticker: str) -> str:
    from config import SECTOR_MAP
    for sector, tickers in SECTOR_MAP.items():
        if ticker in tickers:
            return sector
    return "Diversified"
