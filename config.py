"""
config.py - Central configuration for Indian Stock Advisor
"""

# ─────────────────────────────────────────────
# API Keys
# ─────────────────────────────────────────────
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"   # Replace with your key
CLAUDE_MODEL      = "claude-sonnet-4-20250514"

# ─────────────────────────────────────────────
# Valkey / Redis connection
# ─────────────────────────────────────────────
VALKEY_HOST = "localhost"
VALKEY_PORT = 6379
VALKEY_DB   = 0

# TTL (seconds) for cached data
TTL_PRICE       = 300        # 5 min  – live prices
TTL_HISTORY     = 3600       # 1 hr   – OHLCV history
TTL_FUNDAMENTALS = 86400     # 24 hr  – fundamentals (P/E, EPS …)
TTL_NEWS        = 1800       # 30 min – news feed

# ─────────────────────────────────────────────
# Market settings
# ─────────────────────────────────────────────
HISTORY_PERIOD  = "1y"       # yfinance period for OHLCV
HISTORY_INTERVAL = "1d"      # daily candles

MIN_PRICE       = 20         # filter out sub-₹20 stocks (penny)
MIN_VOLUME      = 50_000     # min avg daily volume
MIN_MARKET_CAP  = 100e7      # ₹100 Cr minimum market cap

# Cap boundaries (market cap in ₹ Crore)
LARGE_CAP_MIN   = 20_000     # ≥ ₹20,000 Cr
MID_CAP_MIN     = 5_000      # ₹5,000 – 20,000 Cr
SMALL_CAP_MIN   = 500        # ₹500 – 5,000 Cr
# below 500 Cr → micro/nano, excluded

# ─────────────────────────────────────────────
# NSE Large Cap stocks (Nifty 50 + Nifty Next 50 sample)
# Format: yfinance ticker with .NS suffix
# ─────────────────────────────────────────────
LARGE_CAP_STOCKS = [
    # Nifty 50 core
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS",
    "LT.NS", "AXISBANK.NS", "ASIANPAINT.NS", "MARUTI.NS", "TITAN.NS",
    "SUNPHARMA.NS", "NESTLEIND.NS", "WIPRO.NS", "ULTRACEMCO.NS", "POWERGRID.NS",
    "NTPC.NS", "ONGC.NS", "TATAMOTORS.NS", "JSWSTEEL.NS", "HCLTECH.NS",
    "BAJFINANCE.NS", "BAJAJFINSV.NS", "ADANIENT.NS", "ADANIPORTS.NS", "COALINDIA.NS",
    "DIVISLAB.NS", "DRREDDY.NS", "CIPLA.NS", "EICHERMOT.NS", "HEROMOTOCO.NS",
    "BPCL.NS", "BRITANNIA.NS", "GRASIM.NS", "HINDALCO.NS", "INDUSINDBK.NS",
    "M&M.NS", "SBILIFE.NS", "HDFCLIFE.NS", "TECHM.NS", "APOLLOHOSP.NS",
    "TATASTEEL.NS", "UPL.NS", "TATACONSUM.NS", "BAJAJ-AUTO.NS", "SHRIRAMFIN.NS",
]

# ─────────────────────────────────────────────
# NSE Mid Cap stocks (Nifty Midcap 100 sample)
# ─────────────────────────────────────────────
MID_CAP_STOCKS = [
    "MUTHOOTFIN.NS", "PERSISTENT.NS", "COFORGE.NS", "LTIM.NS", "MPHASIS.NS",
    "VOLTAS.NS", "GODREJPROP.NS", "OBEROIRLTY.NS", "PHOENIXLTD.NS", "PRESTIGE.NS",
    "AUROPHARMA.NS", "LALPATHLAB.NS", "METROPOLIS.NS", "FORTIS.NS", "MAXHEALTH.NS",
    "INDIAMART.NS", "NAUKRI.NS", "POLICYBZR.NS", "DELHIVERY.NS", "ZOMATO.NS",
    "FEDERALBNK.NS", "IDFCFIRSTB.NS", "BANDHANBNK.NS", "RBLBANK.NS", "CANBK.NS",
    "AARTIIND.NS", "DEEPAKNTR.NS", "PIIND.NS", "UBL.NS", "RADICO.NS",
    "TRENT.NS", "MANYAVAR.NS", "PAGEIND.NS", "BATAIND.NS", "RELAXO.NS",
    "CROMPTON.NS", "HAVELLS.NS", "POLYCAB.NS", "KEI.NS", "APLAPOLLO.NS",
    "ASHOKLEY.NS", "MRF.NS", "BALKRISIND.NS", "ESCORTS.NS", "SWARAJENG.NS",
    "INDUSTOWER.NS", "CESC.NS", "TORNTPOWER.NS", "ADANIGREEN.NS", "TATAPOWER.NS",
]

# ─────────────────────────────────────────────
# NSE Small Cap stocks (Nifty Smallcap 100 sample)
# ─────────────────────────────────────────────
SMALL_CAP_STOCKS = [
    "HAPPSTMNDS.NS", "TANLA.NS", "LATENTVIEW.NS", "ROUTE.NS", "MASTEK.NS",
    "GRANULES.NS", "SUVEN.NS", "GLENMARK.NS", "NATCOPHARM.NS", "SOLARA.NS",
    "KPRMILL.NS", "RAYMOND.NS", "ARVIND.NS", "TRIDENT.NS", "WELSPUNLIV.NS",
    "GREENPLY.NS", "CENTURYPLY.NS", "GREENPANEL.NS", "ASTRAL.NS", "SUPREMEIND.NS",
    "VAIBHAVGBL.NS", "SENCO.NS", "PCJEWELLER.NS", "THANGAMAYL.NS", "GOLDIAM.NS",
    "UJJIVANSFB.NS", "EQUITASBNK.NS", "SURYODAY.NS", "ESAFSFB.NS", "UTKARSHBNK.NS",
    "SAFARI.NS", "VIPIND.NS", "BAJAJELEC.NS", "ORIENTELEC.NS", "SYRMA.NS",
    "CRAFTSMAN.NS", "ELECON.NS", "BECTORFOOD.NS", "KRBL.NS", "KOHINOOR.NS",
    "IOLCP.NS", "FINEORG.NS", "VINATI.NS", "NOCIL.NS", "GALAXYSURF.NS",
    "INDIGRID.NS", "PGHH.NS", "JUBLPHARMA.NS", "HLEGLAS.NS", "SHARDACROP.NS",
]

ALL_STOCKS = LARGE_CAP_STOCKS + MID_CAP_STOCKS + SMALL_CAP_STOCKS

# ─────────────────────────────────────────────
# Fundamental thresholds (hard filters)
# ─────────────────────────────────────────────
FUNDAMENTAL_FILTERS = {
    "max_pe"              : 80,     # P/E ratio upper bound
    "min_pe"              : 0,      # exclude negative P/E (losses)
    "min_roe"             : 10,     # Return on Equity %
    "min_roce"            : 12,     # Return on Capital Employed %
    "max_debt_equity"     : 2.0,    # Debt / Equity ratio
    "min_revenue_growth"  : 5,      # YoY revenue growth %
    "min_profit_margin"   : 5,      # Net profit margin %
    "min_current_ratio"   : 1.0,    # Liquidity check
    "max_peg"             : 3.0,    # PEG ratio (P/E / growth)
}

# ─────────────────────────────────────────────
# Technical indicator settings
# ─────────────────────────────────────────────
TECH = {
    # RSI
    "rsi_period"          : 14,
    "rsi_oversold"        : 40,     # buy zone
    "rsi_overbought"      : 70,     # avoid

    # MACD
    "macd_fast"           : 12,
    "macd_slow"           : 26,
    "macd_signal"         : 9,

    # Bollinger Bands
    "bb_period"           : 20,
    "bb_std"              : 2,

    # Moving averages
    "ema_short"           : 20,
    "ema_medium"          : 50,
    "ema_long"            : 200,

    # ATR (volatility / stop-loss sizing)
    "atr_period"          : 14,

    # Volume
    "vol_avg_period"      : 20,     # days for avg volume
    "vol_surge_factor"    : 1.5,    # current vol must be 1.5x avg

    # ADX (trend strength)
    "adx_period"          : 14,
    "adx_min"             : 20,     # strong trend threshold

    # Stochastic
    "stoch_k"             : 14,
    "stoch_d"             : 3,
    "stoch_oversold"      : 30,
}

# ─────────────────────────────────────────────
# Sectors for grouping
# ─────────────────────────────────────────────
SECTOR_MAP = {
    "Technology"     : ["TCS.NS","INFY.NS","WIPRO.NS","HCLTECH.NS","TECHM.NS",
                        "PERSISTENT.NS","COFORGE.NS","LTIM.NS","MPHASIS.NS",
                        "HAPPSTMNDS.NS","TANLA.NS","LATENTVIEW.NS","ROUTE.NS","MASTEK.NS"],
    "Banking"        : ["HDFCBANK.NS","ICICIBANK.NS","SBIN.NS","KOTAKBANK.NS","AXISBANK.NS",
                        "INDUSINDBK.NS","FEDERALBNK.NS","IDFCFIRSTB.NS","BANDHANBNK.NS",
                        "RBLBANK.NS","CANBK.NS","UJJIVANSFB.NS","EQUITASBNK.NS"],
    "NBFC"           : ["BAJFINANCE.NS","BAJAJFINSV.NS","MUTHOOTFIN.NS","SHRIRAMFIN.NS"],
    "Pharma"         : ["SUNPHARMA.NS","DRREDDY.NS","CIPLA.NS","DIVISLAB.NS","AUROPHARMA.NS",
                        "GRANULES.NS","NATCOPHARM.NS","GLENMARK.NS"],
    "FMCG"           : ["HINDUNILVR.NS","ITC.NS","NESTLEIND.NS","BRITANNIA.NS","TATACONSUM.NS",
                        "UBL.NS","RADICO.NS"],
    "Auto"           : ["MARUTI.NS","TATAMOTORS.NS","EICHERMOT.NS","HEROMOTOCO.NS","M&M.NS",
                        "BAJAJ-AUTO.NS","ASHOKLEY.NS","MRF.NS","BALKRISIND.NS","ESCORTS.NS"],
    "Energy"         : ["RELIANCE.NS","ONGC.NS","BPCL.NS","NTPC.NS","POWERGRID.NS",
                        "ADANIENT.NS","ADANIGREEN.NS","TATAPOWER.NS","TORNTPOWER.NS","CESC.NS"],
    "Metals"         : ["JSWSTEEL.NS","TATASTEEL.NS","HINDALCO.NS","COALINDIA.NS","APLAPOLLO.NS"],
    "Realty"         : ["GODREJPROP.NS","OBEROIRLTY.NS","PHOENIXLTD.NS","PRESTIGE.NS"],
    "Consumer"       : ["TITAN.NS","ASIANPAINT.NS","TRENT.NS","HAVELLS.NS","CROMPTON.NS",
                        "POLYCAB.NS","BATAIND.NS","PAGEIND.NS"],
}
