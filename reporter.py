"""
reporter.py - Console output formatter for stock recommendations
Prints structured, easy-to-read recommendation tables.
"""

from datetime import datetime

# ANSI colours for terminal
RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RED    = "\033[91m"
BLUE   = "\033[94m"
MAGENTA= "\033[95m"
WHITE  = "\033[97m"
DIM    = "\033[2m"
BG_DARK= "\033[40m"


def divider(char="─", width=80, color=DIM):
    print(f"{color}{char * width}{RESET}")


def header(title: str, color=CYAN):
    divider("═", 80, color)
    padding = (80 - len(title) - 2) // 2
    print(f"{color}{'═' * padding} {BOLD}{title}{RESET}{color} {'═' * padding}{RESET}")
    divider("═", 80, color)


def section(title: str, color=YELLOW):
    print()
    divider("─", 80, color)
    print(f"{color}{BOLD}  {title}{RESET}")
    divider("─", 80, color)


def print_fundamental_rec(rec: dict, rank: int):
    """Print a single fundamental recommendation block."""
    ticker  = rec.get("ticker", "N/A")
    name    = rec.get("company_name", ticker)
    sector  = rec.get("sector", "")
    cp      = rec.get("current_price", 0)
    el      = rec.get("entry_price_low", 0)
    eh      = rec.get("entry_price_high", 0)
    tl      = rec.get("target_price_low", 0)
    th      = rec.get("target_price_high", 0)
    ret     = rec.get("expected_return_pct", 0)
    horizon = rec.get("investment_horizon", "")
    thesis  = rec.get("thesis", "")
    strengths = rec.get("key_strengths", [])
    risks     = rec.get("key_risks", [])
    score   = rec.get("fundamental_score", "")

    rank_color = [GREEN, YELLOW, CYAN][rank - 1] if rank <= 3 else WHITE

    print(f"\n  {rank_color}{BOLD}#{rank}  {ticker}  —  {name}{RESET}")
    print(f"  {DIM}Sector: {sector}   |   Horizon: {horizon}   |   Fund Score: {score}{RESET}")
    print()
    print(f"  {WHITE}Current Price   :  {BOLD}₹{cp:,.2f}{RESET}")
    print(f"  {GREEN}Entry Zone      :  {BOLD}₹{el:,.2f}  –  ₹{eh:,.2f}{RESET}")
    print(f"  {MAGENTA}Target Zone     :  {BOLD}₹{tl:,.2f}  –  ₹{th:,.2f}{RESET}")
    print(f"  {YELLOW}Expected Return :  {BOLD}{ret:.1f}%{RESET}")
    print()
    print(f"  {CYAN}Investment Thesis:{RESET}")
    print(f"  {thesis}")
    if strengths:
        print(f"\n  {GREEN}Key Strengths:{RESET}")
        for s in strengths:
            print(f"    {GREEN}✓{RESET} {s}")
    if risks:
        print(f"\n  {RED}Key Risks:{RESET}")
        for r in risks:
            print(f"    {RED}⚠{RESET}  {r}")
    divider("·", 78, DIM)


def print_technical_rec(rec: dict, rank: int):
    """Print a single technical recommendation block."""
    ticker  = rec.get("ticker", "N/A")
    name    = rec.get("company_name", ticker)
    sector  = rec.get("sector", "")
    cp      = rec.get("current_price", 0)
    el      = rec.get("entry_price_low", 0)
    eh      = rec.get("entry_price_high", 0)
    tl      = rec.get("target_price_low", 0)
    th      = rec.get("target_price_high", 0)
    sl      = rec.get("stop_loss", 0)
    ret     = rec.get("expected_return_pct", 0)
    horizon = rec.get("trade_horizon", "")
    setup   = rec.get("setup", "")
    thesis  = rec.get("thesis", "")
    signals = rec.get("signals", [])
    score   = rec.get("tech_score", "")

    rank_color = [GREEN, YELLOW, CYAN][rank - 1] if rank <= 3 else WHITE

    print(f"\n  {rank_color}{BOLD}#{rank}  {ticker}  —  {name}{RESET}")
    print(f"  {DIM}Sector: {sector}   |   Horizon: {horizon}   |   Tech Score: {score}{RESET}")
    print(f"  {BLUE}Setup: {BOLD}{setup}{RESET}")
    print()
    print(f"  {WHITE}Current Price   :  {BOLD}₹{cp:,.2f}{RESET}")
    print(f"  {GREEN}Entry Zone      :  {BOLD}₹{el:,.2f}  –  ₹{eh:,.2f}{RESET}")
    print(f"  {MAGENTA}Target Zone     :  {BOLD}₹{tl:,.2f}  –  ₹{th:,.2f}{RESET}")
    print(f"  {RED}Stop Loss       :  {BOLD}₹{sl:,.2f}{RESET}")
    print(f"  {YELLOW}Expected Return :  {BOLD}{ret:.1f}%{RESET}")
    print()
    print(f"  {CYAN}Technical Rationale:{RESET}")
    print(f"  {thesis}")
    if signals:
        print(f"\n  {BLUE}Signals Triggered:{RESET}")
        for sig in signals:
            print(f"    {BLUE}◆{RESET} {sig}")
    divider("·", 78, DIM)


def print_recommendations(fund_recs: dict, tech_recs: dict, cache_stats: dict = None):
    """Main printer for all recommendations."""
    now = datetime.now().strftime("%d %b %Y  %H:%M IST")

    print()
    header("🇮🇳  INDIAN STOCK ADVISOR  —  AI-POWERED RECOMMENDATIONS", CYAN)
    print(f"\n  {DIM}Generated: {now}   |   Exchange: NSE/BSE{RESET}")

    if cache_stats:
        print(f"  {DIM}Cache: {cache_stats.get('total_keys',0)} keys  |  "
              f"Prices: {cache_stats.get('price_keys',0)}  |  "
              f"Fundamentals: {cache_stats.get('fund_keys',0)}{RESET}")

    # ── FUNDAMENTAL RECOMMENDATIONS ──────────────
    print()
    header("📊  FUNDAMENTAL ANALYSIS  —  LONG-TERM PICKS (1–3 Years)", GREEN)
    print(f"\n  {DIM}Based on: P/E, ROE, Revenue Growth, Profit Margins, Debt/Equity, Current Ratio{RESET}")

    if not fund_recs:
        print(f"\n  {RED}No fundamental recommendations available.{RESET}")
    else:
        caps = [("Large", "🔵 LARGE CAP"), ("Mid", "🟡 MID CAP"), ("Small", "🟢 SMALL CAP")]
        for cap_key, cap_label in caps:
            data = fund_recs.get(cap_key)
            if not data:
                continue
            recs = data.get("recommendations", [])
            outlook = data.get("market_outlook", "")

            section(f"{cap_label}  FUNDAMENTAL PICKS", YELLOW)
            if outlook:
                print(f"  {DIM}Market Context: {outlook}{RESET}")

            for rec in recs:
                print_fundamental_rec(rec, rec.get("rank", 1))

    # ── TECHNICAL RECOMMENDATIONS ─────────────────
    print()
    header("📈  TECHNICAL ANALYSIS  —  SHORT-TO-MEDIUM TERM TRADES", BLUE)
    print(f"\n  {DIM}Based on: EMA Alignment, RSI, MACD, ADX, Bollinger Bands, Stochastic, Volume{RESET}")

    if not tech_recs:
        print(f"\n  {RED}No technical recommendations available.{RESET}")
    else:
        caps = [("Large", "🔵 LARGE CAP"), ("Mid", "🟡 MID CAP"), ("Small", "🟢 SMALL CAP")]
        for cap_key, cap_label in caps:
            data = tech_recs.get(cap_key)
            if not data:
                continue
            recs = data.get("recommendations", [])

            section(f"{cap_label}  TECHNICAL PICKS", BLUE)
            for rec in recs:
                print_technical_rec(rec, rec.get("rank", 1))

    # ── DISCLAIMER ────────────────────────────────
    print()
    divider("═", 80, RED)
    print(f"{RED}{BOLD}  ⚠  DISCLAIMER{RESET}")
    print(f"  {DIM}This is AI-generated analysis for educational purposes only.")
    print(f"  Not SEBI-registered investment advice. Past performance ≠ future results.")
    print(f"  Always consult a SEBI-registered advisor before investing.{RESET}")
    divider("═", 80, RED)
    print()
