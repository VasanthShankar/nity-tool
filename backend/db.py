"""SQLAlchemy models for the trading journal."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Boolean
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import create_engine
import os

Base = declarative_base()


class Snapshot(Base):
    """A point-in-time capture of market state. Always created first.
    A trade may or may not be associated with a snapshot."""
    __tablename__ = "snapshots"

    id = Column(Integer, primary_key=True)
    captured_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Spot + futures
    nifty_spot = Column(Float)
    nifty_fut_ltp = Column(Float)
    fut_premium = Column(Float)  # fut - spot

    # Indicators (5-min)
    vwap = Column(Float)
    rsi_14 = Column(Float)
    ema_21 = Column(Float)
    ema_50 = Column(Float)
    supertrend_value = Column(Float)
    supertrend_direction = Column(String)  # "bullish" or "bearish"

    # Distance metrics (useful for similarity search)
    spot_vs_vwap_pct = Column(Float)  # (spot - vwap) / vwap * 100
    ema21_vs_ema50_pct = Column(Float)

    # Option chain stored as JSON: list of 7 strikes (ATM ± 3)
    # [{strike: 24500, ce_ltp, ce_oi, ce_oi_change, ce_iv, ce_volume,
    #   pe_ltp, pe_oi, pe_oi_change, pe_iv, pe_volume}, ...]
    option_chain = Column(JSON)

    # Optional uploaded screenshot — store as base64 in DB for simplicity
    # For production, swap to object storage (S3/R2)
    screenshot_b64 = Column(Text, nullable=True)

    # Raw blob of anything else captured
    raw_data = Column(JSON, nullable=True)

    trade = relationship("Trade", back_populates="snapshot", uselist=False)


class Trade(Base):
    """A discretionary decision made on a snapshot — either entered or skipped."""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    snapshot_id = Column(Integer, ForeignKey("snapshots.id"), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Decision
    action = Column(String)  # "entered" | "skipped"
    direction = Column(String, nullable=True)  # "bullish" | "bearish" | "neutral"
    instrument = Column(String, nullable=True)  # e.g. "NIFTY25500CE"
    strike = Column(Integer, nullable=True)
    option_type = Column(String, nullable=True)  # "CE" | "PE"
    entry_price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=True)  # lots

    # The most important field — your reasoning
    reasoning = Column(Text)

    # User-applied tags so you can group setups, e.g. "vwap_reversion", "trend_pullback"
    setup_tag = Column(String, nullable=True, index=True)

    # Outcome — filled in after exit
    exit_price = Column(Float, nullable=True)
    exit_at = Column(DateTime, nullable=True)
    pnl = Column(Float, nullable=True)
    mfe = Column(Float, nullable=True)  # max favorable excursion
    mae = Column(Float, nullable=True)  # max adverse excursion
    exit_reason = Column(Text, nullable=True)
    closed = Column(Boolean, default=False)

    snapshot = relationship("Snapshot", back_populates="trade")


# DB engine + session factory
def get_engine():
    url = os.getenv("DATABASE_URL", "sqlite:///./nifty.db")
    # Render gives postgres://, SQLAlchemy 2.x wants postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return create_engine(url, pool_pre_ping=True)


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
