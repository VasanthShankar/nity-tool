"""Kite Connect client wrapper.

Handles the daily access token quirk: Kite requires you to log in once per day
via the browser flow to get a fresh access_token. This module reads the current
token from env. You'll need a small login helper script (see scripts/login.py).
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import pandas as pd
from kiteconnect import KiteConnect

IST = timezone(timedelta(hours=5, minutes=30))

# Nifty 50 instrument token on NSE — stable, but verify via instruments dump if needed
NIFTY_50_TOKEN = 256265  # NSE:NIFTY 50


class KiteClient:
    def __init__(self):
        api_key = os.getenv("KITE_API_KEY")
        access_token = os.getenv("KITE_ACCESS_TOKEN")
        if not api_key or not access_token:
            raise RuntimeError("KITE_API_KEY and KITE_ACCESS_TOKEN must be set")
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self._instruments_cache: Optional[pd.DataFrame] = None
        self._instruments_fetched_at: Optional[datetime] = None

    # ---------- Instruments ----------
    def instruments(self) -> pd.DataFrame:
        """NFO instruments dump, cached for the day."""
        now = datetime.now(IST)
        if (
            self._instruments_cache is None
            or self._instruments_fetched_at is None
            or self._instruments_fetched_at.date() != now.date()
        ):
            data = self.kite.instruments("NFO")
            df = pd.DataFrame(data)
            self._instruments_cache = df
            self._instruments_fetched_at = now
        return self._instruments_cache

    def current_week_nifty_futures(self) -> dict:
        """Returns the nearest-expiry NIFTY future instrument row."""
        df = self.instruments()
        futs = df[
            (df["name"] == "NIFTY")
            & (df["segment"] == "NFO-FUT")
            & (df["instrument_type"] == "FUT")
        ].copy()
        futs["expiry"] = pd.to_datetime(futs["expiry"])
        futs = futs.sort_values("expiry")
        today = datetime.now(IST).date()
        upcoming = futs[futs["expiry"].dt.date >= today]
        if upcoming.empty:
            raise RuntimeError("No upcoming NIFTY futures found")
        return upcoming.iloc[0].to_dict()

    def current_week_nifty_options(self) -> pd.DataFrame:
        """All option contracts of the nearest weekly expiry."""
        df = self.instruments()
        opts = df[
            (df["name"] == "NIFTY")
            & (df["segment"] == "NFO-OPT")
        ].copy()
        opts["expiry"] = pd.to_datetime(opts["expiry"])
        today = datetime.now(IST).date()
        upcoming = opts[opts["expiry"].dt.date >= today]
        if upcoming.empty:
            raise RuntimeError("No upcoming NIFTY options found")
        nearest_expiry = upcoming["expiry"].min()
        return upcoming[upcoming["expiry"] == nearest_expiry]

    # ---------- Quotes ----------
    def quote_ltp(self, instruments: list[str]) -> dict:
        """Returns {instrument: ltp}."""
        q = self.kite.ltp(instruments)
        return {k: v["last_price"] for k, v in q.items()}

    def full_quote(self, instruments: list[str]) -> dict:
        return self.kite.quote(instruments)

    # ---------- Candles ----------
    def candles(self, instrument_token: int, interval: str, lookback_minutes: int) -> pd.DataFrame:
        """Fetch historical candles. interval: 'minute', '3minute', '5minute', '15minute', etc."""
        now = datetime.now(IST)
        frm = now - timedelta(minutes=lookback_minutes)
        data = self.kite.historical_data(
            instrument_token=instrument_token,
            from_date=frm,
            to_date=now,
            interval=interval,
        )
        if not data:
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        return df[["open", "high", "low", "close", "volume"]]

    # ---------- Option chain ----------
    def option_chain_atm(self, spot: float, strikes_each_side: int = 3) -> list[dict]:
        """ATM ± N strikes. Returns a list of dicts with CE+PE data per strike."""
        opts = self.current_week_nifty_options()

        # Nifty strikes are in 50-point intervals
        atm = round(spot / 50) * 50
        target_strikes = [atm + i * 50 for i in range(-strikes_each_side, strikes_each_side + 1)]

        # Build instrument list for batch quote
        rows = opts[opts["strike"].isin(target_strikes)]
        if rows.empty:
            return []

        # Tradingsymbol-based quoting is most reliable
        symbols = [f"NFO:{ts}" for ts in rows["tradingsymbol"].tolist()]
        # Kite has a hard cap on items per quote() call; 14 is fine
        quotes = self.full_quote(symbols)

        chain = []
        for strike in sorted(target_strikes):
            row = {"strike": int(strike)}
            for opt_type, key_prefix in [("CE", "ce"), ("PE", "pe")]:
                match = rows[(rows["strike"] == strike) & (rows["instrument_type"] == opt_type)]
                if match.empty:
                    continue
                ts = match.iloc[0]["tradingsymbol"]
                q = quotes.get(f"NFO:{ts}", {})
                ohlc = q.get("ohlc", {})
                row[f"{key_prefix}_ltp"] = q.get("last_price")
                row[f"{key_prefix}_oi"] = q.get("oi")
                row[f"{key_prefix}_volume"] = q.get("volume")
                # IV is not directly in quote; compute or read 'oi_day_high'/'oi_day_low' if needed
                # For now leave IV as None — many users compute it client-side or use a separate source
                row[f"{key_prefix}_iv"] = None
                row[f"{key_prefix}_prev_close"] = ohlc.get("close")
                # OI change vs day open isn't in quote; we'd need to track snapshots
                row[f"{key_prefix}_oi_change"] = None
            chain.append(row)
        return chain
