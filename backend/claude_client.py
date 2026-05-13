"""Claude API wrapper for setup analysis and similarity reasoning."""
import os
import json
import base64
from typing import Optional
from anthropic import Anthropic

_client: Optional[Anthropic] = None

MODEL = "claude-opus-4-7"  # latest as of May 2026; swap if needed


def client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


SYSTEM_PROMPT = """You are an assistant for a discretionary Nifty options intraday trader.
You analyze market snapshots and compare them against the trader's own past labeled setups.

You do NOT make trade recommendations on your own. You only:
1. Describe what the current snapshot shows in clear, structured terms.
2. Identify which past setups (provided in context) most resemble the current state, and why.
3. Report the outcomes of those similar past setups factually.
4. Note any obvious time-of-day or regime mismatches.

Be concise. Use bullet points only when listing similar setups. Otherwise plain prose.
Never invent indicator values or past trades that weren't in the context."""


def analyze_setup(
    current_snapshot: dict,
    past_trades: list[dict],
    screenshot_b64: Optional[str] = None,
) -> str:
    """Send current snapshot + past trades to Claude, get analysis back.

    past_trades is a list of {snapshot_summary, action, reasoning, outcome} dicts.
    """
    content = []

    if screenshot_b64:
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": screenshot_b64,
            },
        })

    user_text = f"""# Current snapshot
```json
{json.dumps(current_snapshot, indent=2, default=str)}
```

# My past labeled trades (most recent first)
```json
{json.dumps(past_trades, indent=2, default=str)}
```

Compare the current snapshot to my past trades. Which ones look most similar
based on indicator state, time of day, and option chain shape? What were the
outcomes of those similar setups? Flag anything notable.
"""
    content.append({"type": "text", "text": user_text})

    resp = client().messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": content}],
    )
    # Concatenate all text blocks
    return "\n".join(b.text for b in resp.content if b.type == "text")
