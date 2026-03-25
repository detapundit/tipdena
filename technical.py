"""
technical.py - Technical analysis engine
Computes indicators (RSI, MACD, BB, EMA, ADX, Stochastic, Volume) and scores stocks.
"""

import pandas as pd
import pandas_ta as ta
import numpy as np
from config import TECH, MIN_PRICE, MIN_VOLUME
import db


# ─────────────────────────────────────────────
# Compute all indicators for a single stock
# ─────────────────────────────────────────────
def compute_indicators(df: pd.DataFrame) -> dict | None:
    """
    Given a daily OHLCV DataFrame, compute all technical indicators.
    Returns a flat dict of the latest values.
    """
    if df is None or len(df) < 60:
        return None

    df = df.copy()
    df.columns = [c.lower() for c in df.columns]

    try:
        # ── Trend indicators ──────────────────────
        df.ta.ema(length=TECH["ema_short"],  append=True)
        df.ta.ema(length=TECH["ema_medium"], append=True)
        df.ta.ema(length=TECH["ema_long"],   append=True)
        df.ta.adx(length=TECH["adx_period"], append=True)

        # ── Momentum ──────────────────────────────
        df.ta.rsi(length=TECH["rsi_period"], append=True)
        df.ta.macd(
            fast=TECH["macd_fast"],
            slow=TECH["macd_slow"],
            signal=TECH["macd_signal"],
            append=True
        )
        df.ta.stoch(
            k=TECH["stoch_k"],
            d=TECH["stoch_d"],
            append=True
        )

        # ── Volatility ────────────────────────────
        df.ta.bbands(
            length=TECH["bb_period"],
            std=TECH["bb_std"],
            append=True
        )
        df.ta.atr(length=TECH["atr_period"], append=True)

        # ── Volume ────────────────────────────────
        df["vol_avg"] = df["volume"].rolling(TECH["vol_avg_period"]).mean()
        df["vol_ratio"] = df["volume"] / df["vol_avg"].replace(0, np.nan)
        df.ta.obv(append=True)   # On-Balance Volume

        # ── Support / Resistance (pivot) ──────────
        df["pivot"]      = (df["high"] + df["low"] + df["close"]) / 3
        df["resistance1"] = 2 * df["pivot"] - df["low"]
        df["support1"]    = 2 * df["pivot"] - df["high"]

        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last

        # Column name helpers (pandas_ta naming)
        ema_s  = f"EMA_{TECH['ema_short']}"
        ema_m  = f"EMA_{TECH['ema_medium']}"
        ema_l  = f"EMA_{TECH['ema_long']}"
        adx_c  = f"ADX_{TECH['adx_period']}"
        dmp    = f"DMP_{TECH['adx_period']}"
        dmn    = f"DMN_{TECH['adx_period']}"
        rsi_c  = f"RSI_{TECH['rsi_period']}"
        macd_c = f"MACD_{TECH['macd_fast']}_{TECH['macd_slow']}_{TECH['macd_signal']}"
        hist_c = f"MACDh_{TECH['macd_fast']}_{TECH['macd_slow']}_{TECH['macd_signal']}"
        sig_c  = f"MACDs_{TECH['macd_fast']}_{TECH['macd_slow']}_{TECH['macd_signal']}"
        stk_c  = f"STOCHk_{TECH['stoch_k']}_{TECH['stoch_d']}_3"
        std_c  = f"STOCHd_{TECH['stoch_k']}_{TECH['stoch_d']}_3"
        bbu_c  = f"BBU_{TECH['bb_period']}_{float(TECH['bb_std'])}"
        bbm_c  = f"BBM_{TECH['bb_period']}_{float(TECH['bb_std'])}"
        bbl_c  = f"BBL_{TECH['bb_period']}_{float(TECH['bb_std'])}"
        atr_c  = f"ATRr_{TECH['atr_period']}"

        def g(col, default=None):
            return round(float(last[col]), 4) if col in last.index and not pd.isna(last[col]) else default

        def gp(col, default=None):
            return round(float(prev[col]), 4) if col in prev.index and not pd.isna(prev[col]) else default

        price = g("close")
        atr   = g(atr_c)

        indicators = {
            # Price
            "close"       : price,
            "volume"      : int(last.get("volume", 0)),
            "vol_ratio"   : round(float(last.get("vol_ratio", 1)), 2),

            # EMAs
            "ema_20"      : g(ema_s),
            "ema_50"      : g(ema_m),
            "ema_200"     : g(ema_l),
            "price_vs_ema20" : round((price / g(ema_s, price) - 1) * 100, 2) if g(ema_s) else None,
            "price_vs_ema50" : round((price / g(ema_m, price) - 1) * 100, 2) if g(ema_m) else None,
            "price_vs_ema200": round((price / g(ema_l, price) - 1) * 100, 2) if g(ema_l) else None,
            "ema_alignment"  : _ema_alignment(g(ema_s), g(ema_m), g(ema_l)),

            # RSI
            "rsi"         : g(rsi_c),

            # MACD
            "macd"        : g(macd_c),
            "macd_signal" : g(sig_c),
            "macd_hist"   : g(hist_c),
            "macd_crossover": _macd_crossover(g(macd_c), g(sig_c), gp(macd_c), gp(sig_c)),

            # ADX (trend strength)
            "adx"         : g(adx_c),
            "dmp"         : g(dmp),   # +DI (bull)
            "dmn"         : g(dmn),   # -DI (bear)
            "trend_direction": "Bull" if (g(dmp) or 0) > (g(dmn) or 0) else "Bear",

            # Bollinger Bands
            "bb_upper"    : g(bbu_c),
            "bb_mid"      : g(bbm_c),
            "bb_lower"    : g(bbl_c),
            "bb_position" : _bb_position(price, g(bbl_c), g(bbu_c)),

            # Stochastic
            "stoch_k"     : g(stk_c),
            "stoch_d"     : g(std_c),

            # ATR (volatility / stop-loss sizing)
            "atr"         : atr,
            "atr_pct"     : round(atr / price * 100, 2) if atr and price else None,

            # Support / Resistance
            "pivot"       : round(float(last["pivot"]), 2),
            "resistance1" : round(float(last["resistance1"]), 2),
            "support1"    : round(float(last["support1"]), 2),
        }

        return indicators

    except Exception as e:
        return None


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _ema_alignment(ema20, ema50, ema200) -> str:
    if ema20 and ema50 and ema200:
        if ema20 > ema50 > ema200:
            return "Strong Bullish"
        if ema20 < ema50 < ema200:
            return "Strong Bearish"
        if ema20 > ema50:
            return "Mildly Bullish"
    return "Neutral"


def _macd_crossover(macd, signal, prev_macd, prev_signal) -> str:
    if None in (macd, signal, prev_macd, prev_signal):
        return "None"
    if prev_macd <= prev_signal and macd > signal:
        return "Bullish Crossover"
    if prev_macd >= prev_signal and macd < signal:
        return "Bearish Crossover"
    if macd > signal:
        return "Bullish"
    return "Bearish"


def _bb_position(price, lower, upper) -> str:
    if None in (price, lower, upper) or upper == lower:
        return "Unknown"
    pct = (price - lower) / (upper - lower) * 100
    if pct <= 15:
        return "Near Lower Band (Oversold)"
    if pct >= 85:
        return "Near Upper Band (Overbought)"
    if 40 <= pct <= 60:
        return "Mid Band (Neutral)"
    return f"{pct:.0f}% of Band"


# ─────────────────────────────────────────────
# Score a single stock technically (0–100)
# ─────────────────────────────────────────────
def score_technical(ind: dict) -> dict:
    """Score technical indicators. Higher = stronger buy signal."""
    scores = {}

    # 1. Trend (EMA alignment + ADX) — 30 pts
    trend = 0
    ea = ind.get("ema_alignment", "")
    if   "Strong Bullish" in ea: trend += 15
    elif "Mildly Bullish" in ea: trend += 8
    elif "Strong Bearish" in ea: trend -= 5
    else: trend += 2

    adx = ind.get("adx", 0) or 0
    if   adx > 35: trend += 10
    elif adx > 25: trend += 7
    elif adx > 20: trend += 4
    else:          trend += 1

    td = ind.get("trend_direction", "")
    if td == "Bull": trend += 5
    scores["trend"] = max(min(trend, 30), 0)

    # 2. Momentum (RSI, MACD) — 30 pts
    mom = 0
    rsi = ind.get("rsi", 50) or 50
    if   30 <= rsi <= TECH["rsi_oversold"]:  mom += 15   # oversold — prime buy
    elif TECH["rsi_oversold"] < rsi <= 55:   mom += 10   # healthy
    elif 55 < rsi < TECH["rsi_overbought"]:  mom += 5    # heating up
    else:                                     mom += 0    # overbought

    mc = ind.get("macd_crossover", "")
    if   "Bullish Crossover" in mc: mom += 15
    elif "Bullish" in mc:           mom += 8
    elif "Bearish Crossover" in mc: mom -= 5
    else:                           mom += 0
    scores["momentum"] = max(min(mom, 30), 0)

    # 3. Volume confirmation — 20 pts
    vol = 0
    vr = ind.get("vol_ratio", 1) or 1
    if   vr >= 2.0: vol += 20
    elif vr >= 1.5: vol += 14
    elif vr >= 1.0: vol += 8
    else:           vol += 2
    scores["volume"] = min(vol, 20)

    # 4. Bollinger / Stochastic — 20 pts
    bp_score = 0
    bp = ind.get("bb_position", "") or ""
    if   "Oversold"   in bp: bp_score += 12
    elif "Overbought" in bp: bp_score += 0
    elif "Neutral"    in bp: bp_score += 6
    else:                    bp_score += 4

    sk = ind.get("stoch_k", 50) or 50
    sd = ind.get("stoch_d", 50) or 50
    if sk < TECH["stoch_oversold"] and sd < TECH["stoch_oversold"]:
        bp_score += 8
    elif sk < 50:
        bp_score += 4
    scores["oscillator"] = max(min(bp_score, 20), 0)

    total = sum(scores.values())
    scores["total"] = total
    return scores


# ─────────────────────────────────────────────
# Run full technical analysis for all stocks
# ─────────────────────────────────────────────
def run_technical_analysis(prices: dict) -> dict:
    """
    Returns:
    {
      "Large": [ {ticker, indicators, scores, cap, sector}, ... ] sorted by score DESC,
      "Mid"  : [ ... ],
      "Small": [ ... ],
    }
    """
    from data_fetcher import fetch_history, classify_cap, get_sector

    results = {"Large": [], "Mid": [], "Small": []}
    from config import ALL_STOCKS
    print(f"\n  [Technical] Running analysis …")

    computed = 0
    skipped  = 0

    for ticker in ALL_STOCKS:
        price_data = prices.get(ticker, {})
        lp = price_data.get("last_price", 0)

        if lp < MIN_PRICE:
            skipped += 1
            continue

        vol = price_data.get("volume", 0)
        if vol and vol < MIN_VOLUME:
            skipped += 1
            continue

        df = fetch_history(ticker)
        if df is None or len(df) < 60:
            skipped += 1
            continue

        ind = compute_indicators(df)
        if ind is None:
            skipped += 1
            continue

        # Check cached score first
        cached_score = db.load_tech_score(ticker)
        if cached_score and cached_score.get("indicators") == ind:
            scores = cached_score["scores"]
        else:
            scores = score_technical(ind)
            db.save_tech_score(ticker, {"indicators": ind, "scores": scores})

        if scores["total"] < 25:
            skipped += 1
            continue

        cap    = classify_cap(ticker, None)
        sector = get_sector(ticker)
        if cap not in results:
            continue

        results[cap].append({
            "ticker"     : ticker,
            "name"       : ticker.replace(".NS", "").replace(".BO", ""),
            "sector"     : sector,
            "cap"        : cap,
            "indicators" : ind,
            "scores"     : scores,
            "price"      : price_data,
        })
        computed += 1

    for cap in results:
        results[cap].sort(key=lambda x: x["scores"]["total"], reverse=True)

    total = sum(len(v) for v in results.values())
    print(f"  [Technical] Scored: {computed} | Skipped: {skipped} | In pool: {total}")
    for cap in results:
        print(f"    {cap} Cap: {len(results[cap])} stocks in pool")

    return results


# ─────────────────────────────────────────────
# Build summary for AI prompt
# ─────────────────────────────────────────────
def build_technical_prompt_data(ranked: dict, top_n: int = 15) -> dict:
    summary = {}
    for cap, stocks in ranked.items():
        summary[cap] = []
        for s in stocks[:top_n]:
            ind = s["indicators"]
            summary[cap].append({
                "ticker"         : s["ticker"],
                "name"           : s["name"],
                "sector"         : s["sector"],
                "tech_score"     : s["scores"]["total"],
                "current_price"  : ind.get("close"),
                "ema_alignment"  : ind.get("ema_alignment"),
                "rsi"            : ind.get("rsi"),
                "macd_crossover" : ind.get("macd_crossover"),
                "adx"            : ind.get("adx"),
                "trend_dir"      : ind.get("trend_direction"),
                "bb_position"    : ind.get("bb_position"),
                "stoch_k"        : ind.get("stoch_k"),
                "vol_ratio"      : ind.get("vol_ratio"),
                "atr"            : ind.get("atr"),
                "atr_pct"        : ind.get("atr_pct"),
                "support1"       : ind.get("support1"),
                "resistance1"    : ind.get("resistance1"),
                "pivot"          : ind.get("pivot"),
            })
    return summary
