"""FastAPI application for the Nifty options trading journal."""
import os
import base64
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from db import init_db, get_db, Snapshot, Trade
from schemas import (
    SnapshotOut, TradeCreate, TradeOut, TradeOutcome,
    AnalysisRequest, AnalysisResponse,
)
from kite_client import KiteClient, NIFTY_50_TOKEN
from indicators import vwap_anchored, rsi, ema, supertrend
from claude_client import analyze_setup

IST = timezone(timedelta(hours=5, minutes=30))

app = FastAPI(title="Nifty Options Journal")

# CORS — allow your frontend
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy Kite client — don't fail on startup if token isn't set yet
_kite: Optional[KiteClient] = None


def kite() -> KiteClient:
    global _kite
    if _kite is None:
        _kite = KiteClient()
    return _kite


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"ok": True, "time": datetime.now(IST).isoformat()}


# ---------- Snapshot ----------

def _within_trade_window() -> tuple[bool, str]:
    """Time gate: skip 9:15–9:30 and after 14:30 IST."""
    now = datetime.now(IST)
    t = now.time()
    if t < datetime.strptime("09:15", "%H:%M").time():
        return False, "pre-market"
    if t < datetime.strptime("09:30", "%H:%M").time():
        return False, "first-15-min (your filter)"
    if t > datetime.strptime("14:30", "%H:%M").time():
        return False, "after 14:30 (your filter)"
    if t > datetime.strptime("15:30", "%H:%M").time():
        return False, "post-market"
    return True, "ok"


@app.post("/snapshot", response_model=SnapshotOut)
def take_snapshot(
    force: bool = Query(False, description="Override the time window filter"),
    screenshot: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    """Capture a fresh market snapshot from Kite. Optionally attach a screenshot."""
    in_window, reason = _within_trade_window()
    if not in_window and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Outside your trading window: {reason}. Pass force=true to override.",
        )

    k = kite()

    # Spot from NIFTY 50 index quote
    spot_q = k.quote_ltp([f"NSE:NIFTY 50"])
    spot = spot_q.get("NSE:NIFTY 50")
    if spot is None:
        raise HTTPException(500, "Failed to fetch Nifty spot")

    # Current week futures
    fut = k.current_week_nifty_futures()
    fut_token = int(fut["instrument_token"])
    fut_symbol = f"NFO:{fut['tradingsymbol']}"
    fut_q = k.quote_ltp([fut_symbol])
    fut_ltp = fut_q.get(fut_symbol)

    # Candles for indicators
    # 1-min for VWAP (need full session)
    df_1m = k.candles(fut_token, "minute", lookback_minutes=400)
    # 5-min for RSI/EMA/Supertrend
    df_5m = k.candles(fut_token, "5minute", lookback_minutes=400 * 5)

    vwap_val = vwap_anchored(df_1m)
    rsi_val = rsi(df_5m, 14)
    ema21 = ema(df_5m, 21)
    ema50 = ema(df_5m, 50)
    st_val, st_dir = supertrend(df_5m, 10, 2.0)

    # Option chain
    chain = k.option_chain_atm(spot, strikes_each_side=3)

    # Derived
    spot_vs_vwap_pct = (spot - vwap_val) / vwap_val * 100 if vwap_val else None
    ema21_vs_ema50_pct = (ema21 - ema50) / ema50 * 100 if ema50 else None

    # Screenshot to base64 if provided
    screenshot_b64 = None
    if screenshot is not None:
        raw = screenshot.file.read()
        screenshot_b64 = base64.b64encode(raw).decode("ascii")

    snap = Snapshot(
        nifty_spot=spot,
        nifty_fut_ltp=fut_ltp,
        fut_premium=(fut_ltp - spot) if fut_ltp else None,
        vwap=vwap_val,
        rsi_14=rsi_val,
        ema_21=ema21,
        ema_50=ema50,
        supertrend_value=st_val,
        supertrend_direction=st_dir,
        spot_vs_vwap_pct=spot_vs_vwap_pct,
        ema21_vs_ema50_pct=ema21_vs_ema50_pct,
        option_chain=chain,
        screenshot_b64=screenshot_b64,
        raw_data={"fut_tradingsymbol": fut["tradingsymbol"], "fut_expiry": str(fut["expiry"])},
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return snap


@app.get("/snapshot/{snapshot_id}", response_model=SnapshotOut)
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db)):
    snap = db.get(Snapshot, snapshot_id)
    if not snap:
        raise HTTPException(404, "Snapshot not found")
    return snap


# ---------- Trades ----------

@app.post("/trades", response_model=TradeOut)
def create_trade(payload: TradeCreate, db: Session = Depends(get_db)):
    snap = db.get(Snapshot, payload.snapshot_id)
    if not snap:
        raise HTTPException(404, "Snapshot not found")
    # Reject if a trade already exists for this snapshot
    existing = db.query(Trade).filter(Trade.snapshot_id == payload.snapshot_id).first()
    if existing:
        raise HTTPException(400, "Trade already exists for this snapshot")
    trade = Trade(**payload.model_dump())
    db.add(trade)
    db.commit()
    db.refresh(trade)
    return trade


@app.patch("/trades/{trade_id}/close", response_model=TradeOut)
def close_trade(trade_id: int, outcome: TradeOutcome, db: Session = Depends(get_db)):
    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(404, "Trade not found")
    trade.exit_price = outcome.exit_price
    trade.exit_at = datetime.now(IST)
    trade.pnl = outcome.pnl
    trade.mfe = outcome.mfe
    trade.mae = outcome.mae
    trade.exit_reason = outcome.exit_reason
    trade.closed = True
    db.commit()
    db.refresh(trade)
    return trade


@app.get("/trades", response_model=list[TradeOut])
def list_trades(
    limit: int = 50,
    setup_tag: Optional[str] = None,
    closed_only: bool = False,
    db: Session = Depends(get_db),
):
    q = db.query(Trade).order_by(desc(Trade.created_at))
    if setup_tag:
        q = q.filter(Trade.setup_tag == setup_tag)
    if closed_only:
        q = q.filter(Trade.closed.is_(True))
    return q.limit(limit).all()


# ---------- Analysis ----------

def _summarize_trade(trade: Trade, snap: Snapshot) -> dict:
    """Compact representation of a trade for Claude's context."""
    return {
        "trade_id": trade.id,
        "captured_at": snap.captured_at.isoformat() if snap.captured_at else None,
        "indicators": {
            "spot": snap.nifty_spot,
            "fut": snap.nifty_fut_ltp,
            "vwap": snap.vwap,
            "spot_vs_vwap_pct": snap.spot_vs_vwap_pct,
            "rsi_14": snap.rsi_14,
            "ema_21": snap.ema_21,
            "ema_50": snap.ema_50,
            "ema21_vs_ema50_pct": snap.ema21_vs_ema50_pct,
            "supertrend": snap.supertrend_direction,
        },
        "option_chain_summary": _option_chain_shape(snap.option_chain),
        "decision": {
            "action": trade.action,
            "direction": trade.direction,
            "strike": trade.strike,
            "option_type": trade.option_type,
            "entry_price": trade.entry_price,
            "setup_tag": trade.setup_tag,
            "reasoning": trade.reasoning,
        },
        "outcome": {
            "closed": trade.closed,
            "pnl": trade.pnl,
            "mfe": trade.mfe,
            "mae": trade.mae,
            "exit_reason": trade.exit_reason,
        } if trade.action == "entered" else None,
    }


def _option_chain_shape(chain: Optional[list[dict]]) -> Optional[dict]:
    """Reduce chain to a few summary numbers Claude can use."""
    if not chain:
        return None
    total_ce_oi = sum((r.get("ce_oi") or 0) for r in chain)
    total_pe_oi = sum((r.get("pe_oi") or 0) for r in chain)
    pcr = (total_pe_oi / total_ce_oi) if total_ce_oi else None
    atm = chain[len(chain) // 2]
    return {
        "atm_strike": atm.get("strike"),
        "atm_ce_ltp": atm.get("ce_ltp"),
        "atm_pe_ltp": atm.get("pe_ltp"),
        "pcr_atm_band": pcr,
        "strikes_count": len(chain),
    }


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(req: AnalysisRequest, db: Session = Depends(get_db)):
    snap = db.get(Snapshot, req.snapshot_id)
    if not snap:
        raise HTTPException(404, "Snapshot not found")

    # Pull past trades — only closed ones with reasoning are useful as comparisons
    past_q = (
        db.query(Trade, Snapshot)
        .join(Snapshot, Trade.snapshot_id == Snapshot.id)
        .filter(Snapshot.id != snap.id)
        .order_by(desc(Trade.created_at))
        .limit(req.past_trades_limit)
    )
    past = past_q.all()
    past_summaries = [_summarize_trade(t, s) for t, s in past]

    current_summary = {
        "captured_at": snap.captured_at.isoformat(),
        "indicators": {
            "spot": snap.nifty_spot,
            "fut": snap.nifty_fut_ltp,
            "fut_premium": snap.fut_premium,
            "vwap": snap.vwap,
            "spot_vs_vwap_pct": snap.spot_vs_vwap_pct,
            "rsi_14": snap.rsi_14,
            "ema_21": snap.ema_21,
            "ema_50": snap.ema_50,
            "ema21_vs_ema50_pct": snap.ema21_vs_ema50_pct,
            "supertrend_value": snap.supertrend_value,
            "supertrend_direction": snap.supertrend_direction,
        },
        "option_chain": snap.option_chain,
        "option_chain_summary": _option_chain_shape(snap.option_chain),
    }

    analysis_text = analyze_setup(
        current_snapshot=current_summary,
        past_trades=past_summaries,
        screenshot_b64=snap.screenshot_b64 if req.include_screenshot else None,
    )

    return AnalysisResponse(
        snapshot_id=snap.id,
        analysis=analysis_text,
        past_trades_considered=len(past_summaries),
    )
