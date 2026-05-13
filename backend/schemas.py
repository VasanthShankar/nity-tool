"""Pydantic schemas for API requests and responses."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel


class SnapshotOut(BaseModel):
    id: int
    captured_at: datetime
    nifty_spot: Optional[float]
    nifty_fut_ltp: Optional[float]
    fut_premium: Optional[float]
    vwap: Optional[float]
    rsi_14: Optional[float]
    ema_21: Optional[float]
    ema_50: Optional[float]
    supertrend_value: Optional[float]
    supertrend_direction: Optional[str]
    spot_vs_vwap_pct: Optional[float]
    ema21_vs_ema50_pct: Optional[float]
    option_chain: Optional[list[dict]]

    class Config:
        from_attributes = True


class TradeCreate(BaseModel):
    snapshot_id: int
    action: str  # "entered" or "skipped"
    direction: Optional[str] = None
    instrument: Optional[str] = None
    strike: Optional[int] = None
    option_type: Optional[str] = None  # "CE" or "PE"
    entry_price: Optional[float] = None
    quantity: Optional[int] = None
    reasoning: str
    setup_tag: Optional[str] = None


class TradeOutcome(BaseModel):
    exit_price: float
    pnl: float
    mfe: Optional[float] = None
    mae: Optional[float] = None
    exit_reason: Optional[str] = None


class TradeOut(BaseModel):
    id: int
    snapshot_id: int
    created_at: datetime
    action: str
    direction: Optional[str]
    instrument: Optional[str]
    strike: Optional[int]
    option_type: Optional[str]
    entry_price: Optional[float]
    quantity: Optional[int]
    reasoning: str
    setup_tag: Optional[str]
    exit_price: Optional[float]
    pnl: Optional[float]
    mfe: Optional[float]
    mae: Optional[float]
    exit_reason: Optional[str]
    closed: bool

    class Config:
        from_attributes = True


class AnalysisRequest(BaseModel):
    snapshot_id: int
    include_screenshot: bool = True
    past_trades_limit: int = 30


class AnalysisResponse(BaseModel):
    snapshot_id: int
    analysis: str
    past_trades_considered: int
