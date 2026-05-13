"""Indicator calculations.

All functions take a pandas DataFrame with columns: open, high, low, close, volume
and a DatetimeIndex. They return the latest value (a single float or tuple).
"""
import pandas as pd
import numpy as np


def vwap_anchored(df_1min: pd.DataFrame, session_start_hour: int = 9, session_start_minute: int = 15) -> float:
    """VWAP anchored to session start (9:15 IST). Use 1-min candles for accuracy.

    Filters to today's session candles only, then computes cumulative VWAP.
    """
    if df_1min.empty:
        return float("nan")

    today = df_1min.index[-1].date()
    session = df_1min[df_1min.index.date == today]
    if session.empty:
        return float("nan")

    typical = (session["high"] + session["low"] + session["close"]) / 3
    cum_pv = (typical * session["volume"]).cumsum()
    cum_v = session["volume"].cumsum().replace(0, np.nan)
    vwap = cum_pv / cum_v
    return float(vwap.iloc[-1])


def rsi(df: pd.DataFrame, period: int = 14) -> float:
    """Wilder's RSI on close prices."""
    if len(df) < period + 1:
        return float("nan")

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    # Wilder's smoothing
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    return float(rsi_series.iloc[-1])


def ema(df: pd.DataFrame, period: int) -> float:
    """Exponential moving average on close."""
    if len(df) < period:
        return float("nan")
    return float(df["close"].ewm(span=period, adjust=False).mean().iloc[-1])


def atr(df: pd.DataFrame, period: int = 10) -> pd.Series:
    """Average True Range, used inside Supertrend."""
    high_low = df["high"] - df["low"]
    high_close = (df["high"] - df["close"].shift()).abs()
    low_close = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / period, adjust=False).mean()


def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 2.0):
    """Supertrend(period, multiplier).

    Returns (latest_value, direction) where direction is 'bullish' or 'bearish'.
    Standard implementation: when close > upper band, trend is bullish.
    """
    if len(df) < period + 1:
        return float("nan"), "unknown"

    hl2 = (df["high"] + df["low"]) / 2
    atr_series = atr(df, period)

    upper_basic = hl2 + multiplier * atr_series
    lower_basic = hl2 - multiplier * atr_series

    upper = upper_basic.copy()
    lower = lower_basic.copy()

    # Refine bands so they only move in their respective direction
    for i in range(1, len(df)):
        if df["close"].iloc[i - 1] <= upper.iloc[i - 1]:
            upper.iloc[i] = min(upper_basic.iloc[i], upper.iloc[i - 1])
        if df["close"].iloc[i - 1] >= lower.iloc[i - 1]:
            lower.iloc[i] = max(lower_basic.iloc[i], lower.iloc[i - 1])

    # Determine direction
    direction = pd.Series(index=df.index, dtype=object)
    st = pd.Series(index=df.index, dtype=float)
    direction.iloc[0] = "bullish"
    st.iloc[0] = lower.iloc[0]

    for i in range(1, len(df)):
        prev_dir = direction.iloc[i - 1]
        close = df["close"].iloc[i]
        if prev_dir == "bullish":
            if close < lower.iloc[i]:
                direction.iloc[i] = "bearish"
                st.iloc[i] = upper.iloc[i]
            else:
                direction.iloc[i] = "bullish"
                st.iloc[i] = lower.iloc[i]
        else:
            if close > upper.iloc[i]:
                direction.iloc[i] = "bullish"
                st.iloc[i] = lower.iloc[i]
            else:
                direction.iloc[i] = "bearish"
                st.iloc[i] = upper.iloc[i]

    return float(st.iloc[-1]), str(direction.iloc[-1])
