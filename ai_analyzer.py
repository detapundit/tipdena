"""
ai_analyzer.py - Claude AI-powered stock recommendation engine
Sends scored stock data to Claude and gets top 3 picks per cap with entry/target prices.
"""

import json
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL


client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# ─────────────────────────────────────────────
# Fundamental Analysis Prompt
# ─────────────────────────────────────────────
FUNDAMENTAL_SYSTEM = """You are an expert Indian stock market analyst with deep expertise in 
fundamental analysis of BSE/NSE listed companies. You analyse financial metrics to identify 
fundamentally strong stocks for investment.

Your recommendations must be:
- Based strictly on the data provided
- Differentiated across sectors (no two picks from the same sector unless unavoidable)
- Realistic with entry/target prices based on current price and fundamental valuation
- Clear on investment thesis and key risks

Always respond with valid JSON only. No markdown, no explanation outside JSON."""


def build_fundamental_prompt(cap: str, stocks: list, market_news: list) -> str:
    news_text = "\n".join(f"- {n['title']}" for n in market_news[:5]) if market_news else "No recent news available."

    return f"""Analyse the following {cap} Cap Indian stocks and recommend the TOP 3 for long-term investment (1–3 years).

MARKET CONTEXT:
{news_text}

STOCK DATA ({cap} Cap — top {len(stocks)} fundamentally screened):
{json.dumps(stocks, indent=2)}

RULES:
1. Pick exactly 3 stocks (different sectors if possible)
2. Base entry price on current price adjusted for fair value margin of safety
3. Target price must be justified by P/E expansion or earnings growth (12–24 month horizon)
4. Avoid stocks where news indicates serious negative developments
5. Clearly state the investment thesis in 2-3 lines

Respond ONLY with this JSON structure:
{{
  "cap": "{cap}",
  "analysis_type": "Fundamental",
  "recommendations": [
    {{
      "rank": 1,
      "ticker": "TICKER.NS",
      "company_name": "Company Name",
      "sector": "Sector",
      "current_price": 0.0,
      "entry_price_low": 0.0,
      "entry_price_high": 0.0,
      "target_price_low": 0.0,
      "target_price_high": 0.0,
      "expected_return_pct": 0.0,
      "investment_horizon": "12-18 months",
      "thesis": "2-3 line investment thesis",
      "key_strengths": ["strength1", "strength2", "strength3"],
      "key_risks": ["risk1", "risk2"],
      "fundamental_score": 0
    }}
  ],
  "market_outlook": "Brief 1-line market context"
}}"""


# ─────────────────────────────────────────────
# Technical Analysis Prompt
# ─────────────────────────────────────────────
TECHNICAL_SYSTEM = """You are an expert Indian stock market technical analyst with deep expertise 
in chart patterns, momentum indicators, and price action for BSE/NSE listed stocks.

Your trading recommendations must be:
- Based strictly on the technical data provided (RSI, MACD, EMA, ADX, BB, Stochastic, Volume)
- Suitable for short-to-medium term trades (2 weeks to 3 months)
- Include precise entry zones, targets and stop-loss based on support/resistance and ATR
- Differentiated across sectors

Always respond with valid JSON only. No markdown, no explanation outside JSON."""


def build_technical_prompt(cap: str, stocks: list) -> str:
    return f"""Analyse the following {cap} Cap Indian stocks and recommend the TOP 3 for short-to-medium term trading (2 weeks to 3 months).

STOCK TECHNICAL DATA ({cap} Cap — top {len(stocks)} technically screened):
{json.dumps(stocks, indent=2)}

RULES:
1. Pick exactly 3 stocks showing the strongest buy setups (different sectors if possible)
2. Entry price zone: based on support1, pivot, current price — pick optimal accumulation zone
3. Target: based on resistance1, ATR projections (1.5x–2.5x ATR from entry)
4. Stop-loss: 1x ATR below entry (mention in thesis)
5. Prioritise stocks with: bullish EMA alignment, RSI 35-60, MACD bullish, volume surge

Respond ONLY with this JSON structure:
{{
  "cap": "{cap}",
  "analysis_type": "Technical",
  "recommendations": [
    {{
      "rank": 1,
      "ticker": "TICKER.NS",
      "company_name": "Ticker Symbol",
      "sector": "Sector",
      "current_price": 0.0,
      "entry_price_low": 0.0,
      "entry_price_high": 0.0,
      "target_price_low": 0.0,
      "target_price_high": 0.0,
      "stop_loss": 0.0,
      "expected_return_pct": 0.0,
      "trade_horizon": "2-6 weeks",
      "setup": "Name of setup (e.g. EMA Crossover + RSI Reversal)",
      "thesis": "2-3 line technical rationale",
      "signals": ["signal1", "signal2", "signal3"],
      "tech_score": 0
    }}
  ]
}}"""


# ─────────────────────────────────────────────
# Call Claude API
# ─────────────────────────────────────────────
def call_claude(system: str, user_prompt: str, max_tokens: int = 2000) -> dict | None:
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = response.content[0].text.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        return json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"  [AI] JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"  [AI] Claude API error: {e}")
        return None


# ─────────────────────────────────────────────
# Run fundamental AI analysis
# ─────────────────────────────────────────────
def get_fundamental_recommendations(prompt_data: dict, market_news: list) -> dict:
    """Call Claude for each cap category and return structured recommendations."""
    results = {}
    caps = ["Large", "Mid", "Small"]

    print("\n  [AI] Requesting fundamental recommendations from Claude …")
    for cap in caps:
        stocks = prompt_data.get(cap, [])
        if not stocks:
            print(f"  [AI] No {cap} cap stocks in pool, skipping")
            continue

        print(f"  [AI] Analysing {len(stocks)} {cap} cap stocks for fundamental picks …")
        prompt  = build_fundamental_prompt(cap, stocks, market_news)
        result  = call_claude(FUNDAMENTAL_SYSTEM, prompt, max_tokens=2500)

        if result:
            results[cap] = result
            print(f"  [AI] ✓ {cap} Cap fundamental recs received")
        else:
            print(f"  [AI] ✗ {cap} Cap fundamental analysis failed")

    return results


# ─────────────────────────────────────────────
# Run technical AI analysis
# ─────────────────────────────────────────────
def get_technical_recommendations(prompt_data: dict) -> dict:
    """Call Claude for each cap category and return structured technical recs."""
    results = {}
    caps = ["Large", "Mid", "Small"]

    print("\n  [AI] Requesting technical recommendations from Claude …")
    for cap in caps:
        stocks = prompt_data.get(cap, [])
        if not stocks:
            print(f"  [AI] No {cap} cap stocks in pool, skipping")
            continue

        print(f"  [AI] Analysing {len(stocks)} {cap} cap stocks for technical picks …")
        prompt  = build_technical_prompt(cap, stocks)
        result  = call_claude(TECHNICAL_SYSTEM, prompt, max_tokens=2500)

        if result:
            results[cap] = result
            print(f"  [AI] ✓ {cap} Cap technical recs received")
        else:
            print(f"  [AI] ✗ {cap} Cap technical analysis failed")

    return results
