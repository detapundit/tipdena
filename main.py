"""
main.py - Indian Stock Advisor
Orchestrates the full pipeline:
  1. Fetch prices for all NSE/BSE stocks
  2. Fetch OHLCV history
  3. Fetch fundamentals
  4. Fetch news feeds
  5. Run fundamental analysis + scoring
  6. Run technical analysis + scoring
  7. AI-powered top-3 picks per cap (Claude)
  8. Print recommendations to console

Usage:
  python main.py                  # full run
  python main.py --tech-only      # technical recs only (faster)
  python main.py --fund-only      # fundamental recs only
  python main.py --clear-cache    # wipe Valkey cache and re-fetch everything
"""

import sys
import time
import argparse
from datetime import datetime

# ─────────────────────────────────────────────
# Argument parsing
# ─────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Indian Stock Advisor")
parser.add_argument("--tech-only",    action="store_true", help="Technical analysis only")
parser.add_argument("--fund-only",    action="store_true", help="Fundamental analysis only")
parser.add_argument("--clear-cache",  action="store_true", help="Clear Valkey cache before run")
parser.add_argument("--stocks",       nargs="+",           help="Analyse specific tickers only")
args = parser.parse_args()

# ─────────────────────────────────────────────
# Imports
# ─────────────────────────────────────────────
import db
import data_fetcher as df
import fundamental as fa
import technical   as ta
import ai_analyzer as ai
import reporter
from config import ALL_STOCKS, LARGE_CAP_STOCKS, MID_CAP_STOCKS, SMALL_CAP_STOCKS


def print_step(n: int, title: str):
    print(f"\n\033[96m{'─'*60}\033[0m")
    print(f"\033[1m\033[96m  STEP {n}: {title}\033[0m")
    print(f"\033[96m{'─'*60}\033[0m")


def check_valkey():
    """Verify Valkey is running before proceeding."""
    if not db.ping():
        print("\n  \033[91m[ERROR] Cannot connect to Valkey.")
        print("  Please start Valkey with:  valkey-server  or  redis-server\033[0m")
        print("  Install: sudo apt install valkey  (Ubuntu)")
        print("           brew install valkey       (macOS)\n")
        sys.exit(1)
    print("  \033[92m[DB] Valkey connection OK\033[0m")


def main():
    start_time = time.time()

    print("\n\033[1m\033[96m" + "═"*60)
    print("  🇮🇳  INDIAN STOCK ADVISOR  —  STARTING UP")
    print("═"*60 + "\033[0m")
    print(f"  Run time : {datetime.now().strftime('%d %b %Y %H:%M:%S IST')}")
    print(f"  Mode     : {'Technical only' if args.tech_only else 'Fundamental only' if args.fund_only else 'Full analysis'}")
    print(f"  Stocks   : {len(args.stocks) if args.stocks else len(ALL_STOCKS)} tickers")

    # ── Valkey check ──────────────────────────
    print_step(1, "Checking Valkey connection")
    check_valkey()

    if args.clear_cache:
        print("  \033[93m[Cache] Clearing all cached data …\033[0m")
        for key in db.keys_matching("*"):
            db.delete(key)
        print("  \033[92m[Cache] Cleared.\033[0m")

    stocks = args.stocks if args.stocks else ALL_STOCKS

    # ── Fetch prices ──────────────────────────
    print_step(2, "Fetching latest prices (NSE/BSE)")
    prices = df.fetch_all_prices(stocks)

    if not prices:
        print("  \033[91m[ERROR] Could not fetch any prices. Check internet connection.\033[0m")
        sys.exit(1)

    valid_prices = {t: p for t, p in prices.items() if p.get("last_price", 0) > 0}
    print(f"  \033[92m[Prices] {len(valid_prices)} stocks with valid prices\033[0m")

    # ── Fetch market news ─────────────────────
    print_step(3, "Fetching market & stock news")
    market_news = df.fetch_market_news()
    print(f"  \033[92m[News] {len(market_news)} market news items fetched\033[0m")

    # Fetch stock-level news for top candidates
    top_tickers = list(valid_prices.keys())[:60]
    news_count = 0
    for ticker in top_tickers:
        n = df.fetch_stock_news(ticker)
        if n:
            news_count += 1
        time.sleep(0.1)
    print(f"  \033[92m[News] Stock news fetched for {news_count} tickers\033[0m")

    fund_recs = {}
    tech_recs = {}

    # ═══════════════════════════════════════════
    # FUNDAMENTAL ANALYSIS PATH
    # ═══════════════════════════════════════════
    if not args.tech_only:
        print_step(4, "Fetching fundamentals (may take 2-3 minutes)")
        fundamentals = df.fetch_all_fundamentals(stocks)

        if not fundamentals:
            print("  \033[91m[WARNING] No fundamental data fetched. Skipping fundamental analysis.\033[0m")
        else:
            print_step(5, "Running fundamental scoring & filtering")
            fund_ranked = fa.run_fundamental_analysis(fundamentals, valid_prices)

            print_step(6, "AI fundamental recommendations (Claude)")
            from fundamental import build_fundamental_prompt_data
            fund_prompt_data = build_fundamental_prompt_data(fund_ranked, top_n=15)
            fund_recs = ai.get_fundamental_recommendations(fund_prompt_data, market_news)

            # Cache recommendations
            db.save_recommendations("fundamental", fund_recs)

    # ═══════════════════════════════════════════
    # TECHNICAL ANALYSIS PATH
    # ═══════════════════════════════════════════
    if not args.fund_only:
        print_step(7 if not args.tech_only else 4, "Computing technical indicators")
        tech_ranked = ta.run_technical_analysis(valid_prices)

        print_step(8 if not args.tech_only else 5, "AI technical recommendations (Claude)")
        from technical import build_technical_prompt_data
        tech_prompt_data = build_technical_prompt_data(tech_ranked, top_n=15)
        tech_recs = ai.get_technical_recommendations(tech_prompt_data)

        # Cache recommendations
        db.save_recommendations("technical", tech_recs)

    # ── Print results ─────────────────────────
    stats = db.cache_stats()
    reporter.print_recommendations(fund_recs, tech_recs, stats)

    elapsed = time.time() - start_time
    print(f"  \033[2mTotal run time: {elapsed:.1f}s\033[0m\n")


if __name__ == "__main__":
    main()
