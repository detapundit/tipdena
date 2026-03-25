"""
db.py - Valkey (Redis-compatible) cache layer
All stock data, prices, fundamentals, news are stored here for fast access.
"""

import json
import pickle
import valkey
from datetime import datetime
from config import VALKEY_HOST, VALKEY_PORT, VALKEY_DB

# ─────────────────────────────────────────────
# Connection
# ─────────────────────────────────────────────
_client = None

def get_client() -> valkey.Valkey:
    global _client
    if _client is None:
        _client = valkey.Valkey(
            host=VALKEY_HOST,
            port=VALKEY_PORT,
            db=VALKEY_DB,
            decode_responses=False,   # we handle encoding ourselves
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
        _client.ping()
        print(f"  [DB] Connected to Valkey at {VALKEY_HOST}:{VALKEY_PORT}")
    return _client


def ping() -> bool:
    try:
        return get_client().ping()
    except Exception as e:
        print(f"  [DB] Valkey ping failed: {e}")
        return False


# ─────────────────────────────────────────────
# Generic helpers
# ─────────────────────────────────────────────
def _key(*parts) -> str:
    return ":".join(str(p) for p in parts)


def set_json(key: str, value, ttl: int = 0):
    """Store any JSON-serialisable value."""
    raw = json.dumps(value, default=str).encode()
    r = get_client()
    if ttl:
        r.setex(key, ttl, raw)
    else:
        r.set(key, raw)


def get_json(key: str):
    raw = get_client().get(key)
    if raw is None:
        return None
    return json.loads(raw.decode())


def set_pickle(key: str, value, ttl: int = 0):
    """Store DataFrame or complex objects via pickle."""
    raw = pickle.dumps(value)
    r = get_client()
    if ttl:
        r.setex(key, ttl, raw)
    else:
        r.set(key, raw)


def get_pickle(key: str):
    raw = get_client().get(key)
    if raw is None:
        return None
    return pickle.loads(raw)


def exists(key: str) -> bool:
    return bool(get_client().exists(key))


def delete(key: str):
    get_client().delete(key)


def keys_matching(pattern: str):
    return [k.decode() for k in get_client().keys(pattern)]


# ─────────────────────────────────────────────
# Domain-specific store / retrieve
# ─────────────────────────────────────────────

# --- Live price ---
def save_price(ticker: str, data: dict, ttl: int):
    set_json(_key("price", ticker), data, ttl)

def load_price(ticker: str):
    return get_json(_key("price", ticker))


# --- OHLCV history (DataFrame via pickle) ---
def save_history(ticker: str, df, ttl: int):
    set_pickle(_key("history", ticker), df, ttl)

def load_history(ticker: str):
    return get_pickle(_key("history", ticker))


# --- Fundamentals ---
def save_fundamentals(ticker: str, data: dict, ttl: int):
    set_json(_key("fundamentals", ticker), data, ttl)

def load_fundamentals(ticker: str):
    return get_json(_key("fundamentals", ticker))


# --- News ---
def save_news(ticker: str, articles: list, ttl: int):
    set_json(_key("news", ticker), articles, ttl)

def load_news(ticker: str):
    return get_json(_key("news", ticker)) or []


def save_market_news(articles: list, ttl: int):
    set_json("market:news", articles, ttl)

def load_market_news():
    return get_json("market:news") or []


# --- Technical scores ---
def save_tech_score(ticker: str, score: dict, ttl: int = 3600):
    set_json(_key("tech_score", ticker), score, ttl)

def load_tech_score(ticker: str):
    return get_json(_key("tech_score", ticker))


# --- Fundamental scores ---
def save_fund_score(ticker: str, score: dict, ttl: int = 86400):
    set_json(_key("fund_score", ticker), score, ttl)

def load_fund_score(ticker: str):
    return get_json(_key("fund_score", ticker))


# --- Run metadata ---
def save_run_meta(meta: dict):
    set_json("run:meta", meta)

def load_run_meta():
    return get_json("run:meta") or {}


# --- Recommendations (final AI output) ---
def save_recommendations(rec_type: str, data: dict):
    set_json(_key("recommendations", rec_type), data)

def load_recommendations(rec_type: str):
    return get_json(_key("recommendations", rec_type))


# ─────────────────────────────────────────────
# Cache stats helper
# ─────────────────────────────────────────────
def cache_stats() -> dict:
    r = get_client()
    info = r.info("keyspace")
    all_keys = keys_matching("*")
    return {
        "total_keys" : len(all_keys),
        "price_keys" : len(keys_matching("price:*")),
        "history_keys": len(keys_matching("history:*")),
        "fund_keys"  : len(keys_matching("fundamentals:*")),
        "news_keys"  : len(keys_matching("news:*")),
        "keyspace"   : str(info),
    }
