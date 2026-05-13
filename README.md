# Nifty Options Journal

A personal discretionary intraday trading journal for Nifty index options on Kite.
Captures live market state via Kite Connect, lets you log every decision with
reasoning, and uses Claude to find similar past setups when you're deciding what
to do next.

This is a journal that learns from your own labeled history — not a signal
generator, not a "model" that predicts trades. The intelligence comes from your
own reasoning text plus structured indicator state, retrieved and compared by
Claude on demand.

## Stack

- **Backend:** FastAPI + SQLAlchemy + Postgres
- **Frontend:** React + Vite + Tailwind
- **Data:** Kite Connect API (live spot, futures, option chain)
- **Indicators:** VWAP (anchored), RSI(14), EMA 21/50, Supertrend(10, 2) — all 5-min
- **Intelligence:** Anthropic Claude API for similarity reasoning across past trades
- **Host:** Render (free tier)

## What it captures per snapshot

- Nifty spot + current-week futures LTP and premium
- VWAP, RSI(14), EMA 21, EMA 50, Supertrend(10, 2) on the 5-min futures chart
- Derived: spot-vs-VWAP %, EMA21-vs-EMA50 %, supertrend direction
- Option chain: ATM ± 3 strikes with CE/PE LTP, OI, volume
- Optional uploaded screenshot

## Time gates

- Refuses snapshots between 9:15–9:30 (your first-15-min filter)
- Refuses snapshots after 14:30 (your no-new-trades filter)
- Override with `force=true` if you ever need to

## Local setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your real keys
```

Get your daily Kite access token:

```bash
python scripts/login.py
# Follow the prompts, then paste the printed access_token into .env
```

Run the API:

```bash
uvicorn main:app --reload
# API now live at http://localhost:8000, docs at http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

## Deploy to Render

1. Push this repo to GitHub.
2. In Render, "New +" → "Blueprint" → select your repo. It'll pick up
   `render.yaml` and provision the API service, the static frontend, and the
   free Postgres database.
3. After services are created, fill in the env vars in the Render dashboard:
   - `nifty-tool-api`: `KITE_API_KEY`, `KITE_API_SECRET`, `KITE_ACCESS_TOKEN`,
     `ANTHROPIC_API_KEY`, `FRONTEND_URL` (set to your `nifty-tool-web` URL)
   - `nifty-tool-web`: `VITE_API_BASE` (set to your `nifty-tool-api` URL)
4. Trigger a manual deploy on both services after env vars are set.

### The daily Kite token rotation

Kite access tokens expire every day at ~6 AM IST. You'll need to refresh the
`KITE_ACCESS_TOKEN` env var on Render every morning before trading:

1. Run `python scripts/login.py` locally
2. Copy the new access token
3. Paste it into Render → `nifty-tool-api` → Environment → `KITE_ACCESS_TOKEN`
4. Save (Render auto-redeploys, takes ~1 min)

There's no way around this — Kite's design requires daily interactive login.
You can build a small Playwright/Selenium auto-login if you want, but that's
a future enhancement.

## Daily workflow

1. ~9:25 AM: refresh Kite token, open the app
2. Pull up your Kite chart, watch for your setup
3. When you see something interesting → click "▸ take snapshot" (optionally
   attach the chart screenshot)
4. Click "ask claude" → it pulls your last 30 trades and shows you which past
   setups are most similar and what happened to them
5. Decide: enter or skip. Either way, click "Save" with your reasoning.
6. After exit (or end of day), open the trade in History and click "log outcome"
   with the actual P&L.

## What makes this useful

The first 50 trades you log are not useful. Period. The model has nothing to
compare against. Around trade 100–150, the similarity matching starts to surface
genuinely useful patterns. By trade 300, you'll see your edges and your leaks
written in your own words next to actual outcomes.

This is the real "training" — you labeling your own decisions, consistently,
over months. The app just makes it easy to look up.

## Things NOT included (yet)

- IV calculation (Kite quote() doesn't return IV directly; needs Black-Scholes
  with a risk-free rate input)
- OI change vs previous candle (requires storing time-series; current version
  stores point-in-time only)
- India VIX (easy to add — needs another quote() call for `NSE:INDIA VIX`)
- Auto-square-off at 3:20
- Order placement (intentionally — keep the human in the loop)
- Auto-snapshot every N minutes (could be a future cron job)

Add them as you need them. The code is small enough to read in one sitting.

## Cost

- Render free tier: $0 (services sleep after 15 min of inactivity; free Postgres
  expires after 90 days, then $7/mo)
- Kite Connect: ₹2000/month
- Anthropic API: usage-based. With 30 past trades + a screenshot per analyze
  call, expect roughly ₹2–6 per analysis. If you call it 5x per trading day,
  that's ~₹500–1500/month.

Total: ~₹3000–4000/month for a personal tool that journals your trades and
gives you on-demand similarity search across your own history.
