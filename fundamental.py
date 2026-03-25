"""
fundamental.py - Fundamental analysis engine
Filters stocks by financial health, scores them, ranks top picks per cap/sector.
"""

from config import FUNDAMENTAL_FILTERS, MIN_PRICE, MIN_VOLUME, MIN_MARKET_CAP
import db


# ─────────────────────────────────────────────
# Hard filter — removes fundamentally weak stocks
# ─────────────────────────────────────────────
def passes_filters(fund: dict, price: dict = None) -> tuple[bool, list]:
    """
    Returns (passes: bool, reasons: list of failed checks).
    A stock must pass ALL hard filters to be considered.
    """
    reasons = []
    f = FUNDAMENTAL_FILTERS

    # Price filter — no penny stocks
    if price:
        lp = price.get("last_price", 0)
        if lp < MIN_PRICE:
            reasons.append(f"Penny stock (₹{lp} < ₹{MIN_PRICE})")
        vol = price.get("volume", 0)
        if vol and vol < MIN_VOLUME:
            reasons.append(f"Low volume ({vol:,} < {MIN_VOLUME:,})")

    # Market cap filter
    mcap = fund.get("market_cap_cr")
    if mcap and mcap * 1e7 < MIN_MARKET_CAP:
        reasons.append(f"Market cap too small (₹{mcap:.0f} Cr)")

    # P/E ratio
    pe = fund.get("pe_ratio")
    if pe is not None:
        if pe <= f["min_pe"]:
            reasons.append(f"Negative/zero P/E ({pe})")
        elif pe > f["max_pe"]:
            reasons.append(f"Very high P/E ({pe} > {f['max_pe']})")

    # ROE
    roe = fund.get("roe_pct")
    if roe is not None and roe < f["min_roe"]:
        reasons.append(f"Low ROE ({roe:.1f}% < {f['min_roe']}%)")

    # Debt/Equity
    de = fund.get("debt_equity")
    if de is not None and de > f["max_debt_equity"]:
        reasons.append(f"High D/E ({de:.2f} > {f['max_debt_equity']})")

    # Profit margin
    pm = fund.get("profit_margin_pct")
    if pm is not None and pm < f["min_profit_margin"]:
        reasons.append(f"Low profit margin ({pm:.1f}% < {f['min_profit_margin']}%)")

    # Current ratio
    cr = fund.get("current_ratio")
    if cr is not None and cr < f["min_current_ratio"]:
        reasons.append(f"Poor liquidity (current ratio {cr:.2f} < {f['min_current_ratio']})")

    return len(reasons) == 0, reasons


# ─────────────────────────────────────────────
# Score a single stock (0–100)
# ─────────────────────────────────────────────
def score_stock(fund: dict) -> dict:
    """
    Returns a dict with component scores and a total score (0–100).
    Higher = better fundamentals.
    """
    scores = {}

    # 1. Valuation (P/E, P/B, PEG) — 25 pts
    val_score = 0
    pe = fund.get("pe_ratio")
    if pe:
        if   pe < 15: val_score += 10
        elif pe < 25: val_score += 8
        elif pe < 40: val_score += 5
        else:         val_score += 2

    pb = fund.get("pb_ratio")
    if pb:
        if   pb < 1:  val_score += 8
        elif pb < 3:  val_score += 6
        elif pb < 6:  val_score += 3
        else:         val_score += 1

    peg = fund.get("peg_ratio")
    if peg:
        if   peg < 1:  val_score += 7
        elif peg < 2:  val_score += 5
        elif peg < 3:  val_score += 2
        else:          val_score += 0
    scores["valuation"] = min(val_score, 25)

    # 2. Profitability (ROE, margins) — 25 pts
    prof_score = 0
    roe = fund.get("roe_pct")
    if roe:
        if   roe > 25: prof_score += 12
        elif roe > 18: prof_score += 9
        elif roe > 12: prof_score += 6
        else:          prof_score += 2

    pm = fund.get("profit_margin_pct")
    if pm:
        if   pm > 20: prof_score += 8
        elif pm > 12: prof_score += 6
        elif pm > 7:  prof_score += 3
        else:         prof_score += 1

    om = fund.get("operating_margin_pct")
    if om:
        if   om > 25: prof_score += 5
        elif om > 15: prof_score += 3
        else:         prof_score += 1
    scores["profitability"] = min(prof_score, 25)

    # 3. Growth (revenue + earnings) — 25 pts
    grow_score = 0
    rg = fund.get("revenue_growth_pct")
    if rg:
        if   rg > 25: grow_score += 13
        elif rg > 15: grow_score += 10
        elif rg > 8:  grow_score += 6
        elif rg > 0:  grow_score += 3
        else:         grow_score += 0

    eg = fund.get("earnings_growth_pct")
    if eg:
        if   eg > 25: grow_score += 12
        elif eg > 15: grow_score += 9
        elif eg > 5:  grow_score += 5
        elif eg > 0:  grow_score += 2
        else:         grow_score += 0
    scores["growth"] = min(grow_score, 25)

    # 4. Financial health (D/E, current ratio) — 15 pts
    health_score = 0
    de = fund.get("debt_equity")
    if de is not None:
        if   de < 0.3: health_score += 8
        elif de < 0.7: health_score += 6
        elif de < 1.2: health_score += 4
        else:          health_score += 1

    cr = fund.get("current_ratio")
    if cr:
        if   cr > 2.5: health_score += 7
        elif cr > 1.5: health_score += 5
        elif cr > 1.0: health_score += 3
        else:          health_score += 0
    scores["financial_health"] = min(health_score, 15)

    # 5. Position from 52w high/low — 10 pts (value opportunity)
    pos_score = 0
    high = fund.get("52w_high")
    low  = fund.get("52w_low")
    if high and low and high > low:
        # lower in range = more value opportunity
        range_pct = (high - low) / high * 100
        if range_pct > 30:    # wide range
            pos_score = 10
        elif range_pct > 15:
            pos_score = 7
        else:
            pos_score = 4
    scores["value_opportunity"] = pos_score

    total = sum(scores.values())
    scores["total"] = total
    return scores


# ─────────────────────────────────────────────
# Filter + rank stocks per cap category
# ─────────────────────────────────────────────
def run_fundamental_analysis(fundamentals: dict, prices: dict) -> dict:
    """
    Returns:
    {
      "Large": [ {ticker, fund, scores, cap, sector, news_headlines}, ... ],
      "Mid"  : [ ... ],
      "Small": [ ... ],
    }
    All lists sorted by total score DESC.
    """
    from data_fetcher import classify_cap, get_sector

    results = {"Large": [], "Mid": [], "Small": []}
    passed = 0
    failed = 0

    print(f"\n  [Fundamental] Analysing {len(fundamentals)} stocks …")

    for ticker, fund in fundamentals.items():
        price = prices.get(ticker)

        # Hard filter
        ok, fail_reasons = passes_filters(fund, price)
        if not ok:
            failed += 1
            continue

        # Score
        scores = score_stock(fund)
        if scores["total"] < 30:   # minimum quality bar
            failed += 1
            continue

        cap     = classify_cap(ticker, fund.get("market_cap_cr"))
        sector  = get_sector(ticker)
        if cap not in results:
            failed += 1
            continue

        # Load cached news headlines
        news = db.load_news(ticker)
        headlines = [n["title"] for n in news[:3]] if news else []

        results[cap].append({
            "ticker"    : ticker,
            "name"      : fund.get("company_name", ticker),
            "sector"    : sector,
            "cap"       : cap,
            "fund"      : fund,
            "scores"    : scores,
            "headlines" : headlines,
            "price"     : price,
        })
        passed += 1

    # Sort each cap by total score
    for cap in results:
        results[cap].sort(key=lambda x: x["scores"]["total"], reverse=True)

    total_filtered = sum(len(v) for v in results.values())
    print(f"  [Fundamental] Passed: {passed} | Filtered out: {failed} | Scored: {total_filtered}")
    for cap in results:
        print(f"    {cap} Cap: {len(results[cap])} stocks in pool")

    return results


# ─────────────────────────────────────────────
# Build summary for AI
# ─────────────────────────────────────────────
def build_fundamental_prompt_data(ranked: dict, top_n: int = 15) -> dict:
    """Prepare top-N stocks per cap as structured data for AI prompt."""
    summary = {}
    for cap, stocks in ranked.items():
        summary[cap] = []
        for s in stocks[:top_n]:
            f = s["fund"]
            summary[cap].append({
                "ticker"         : s["ticker"],
                "name"           : s["name"],
                "sector"         : s["sector"],
                "fund_score"     : s["scores"]["total"],
                "pe"             : f.get("pe_ratio"),
                "pb"             : f.get("pb_ratio"),
                "roe_pct"        : f.get("roe_pct"),
                "profit_margin"  : f.get("profit_margin_pct"),
                "revenue_growth" : f.get("revenue_growth_pct"),
                "earnings_growth": f.get("earnings_growth_pct"),
                "debt_equity"    : f.get("debt_equity"),
                "market_cap_cr"  : f.get("market_cap_cr"),
                "52w_high"       : f.get("52w_high"),
                "52w_low"        : f.get("52w_low"),
                "current_price"  : s["price"]["last_price"] if s["price"] else None,
                "recent_news"    : s["headlines"],
            })
    return summary
