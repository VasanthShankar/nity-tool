import { useRef, useState } from "react";

function Cell({ label, value, suffix, tone }) {
  const toneClass =
    tone === "bull" ? "text-bull" : tone === "bear" ? "text-bear" : "text-text";
  return (
    <div className="border-l border-border pl-3 py-1">
      <div className="text-[10px] uppercase tracking-widest text-muted">
        {label}
      </div>
      <div className={`numeric text-sm ${toneClass} mt-0.5`}>
        {value ?? "—"}
        {suffix && <span className="text-muted text-xs ml-1">{suffix}</span>}
      </div>
    </div>
  );
}

function fmt(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return null;
  return Number(n).toLocaleString("en-IN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export default function SnapshotPanel({ snapshot, loading, onCapture, onAnalyze }) {
  const fileRef = useRef(null);
  const [file, setFile] = useState(null);
  const [force, setForce] = useState(false);

  const s = snapshot;
  const stTone = s?.supertrend_direction === "bullish" ? "bull" : s?.supertrend_direction === "bearish" ? "bear" : null;
  const vwapTone = s?.spot_vs_vwap_pct == null ? null : s.spot_vs_vwap_pct > 0 ? "bull" : "bear";
  const emaTone = s?.ema21_vs_ema50_pct == null ? null : s.ema21_vs_ema50_pct > 0 ? "bull" : "bear";

  return (
    <section className="border border-border bg-panel">
      <header className="border-b border-border px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-accent text-xs numeric">●</span>
          <h2 className="text-xs uppercase tracking-widest text-muted">
            Snapshot
          </h2>
          {s && (
            <span className="text-xs numeric text-muted">
              #{s.id} · {new Date(s.captured_at).toLocaleTimeString("en-IN", { hour12: false, timeZone: "Asia/Kolkata" })}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <label className="text-[10px] uppercase tracking-wider text-muted flex items-center gap-1.5 cursor-pointer">
            <input
              type="checkbox"
              checked={force}
              onChange={(e) => setForce(e.target.checked)}
              className="accent-accent"
            />
            override window
          </label>
        </div>
      </header>

      <div className="p-4">
        <div className="flex flex-wrap items-center gap-2 mb-4">
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="hidden"
          />
          <button
            onClick={() => fileRef.current?.click()}
            className="text-xs numeric uppercase tracking-wider px-3 py-1.5 border border-border hover:border-muted transition-colors"
          >
            {file ? file.name.slice(0, 24) : "+ screenshot"}
          </button>
          <button
            disabled={loading}
            onClick={() => onCapture(file, force)}
            className="text-xs numeric uppercase tracking-wider px-3 py-1.5 border border-accent text-accent hover:bg-accent/10 transition-colors disabled:opacity-40"
          >
            {loading ? "▸ fetching…" : "▸ take snapshot"}
          </button>
          {s && (
            <button
              disabled={loading}
              onClick={onAnalyze}
              className="text-xs numeric uppercase tracking-wider px-3 py-1.5 border border-border hover:border-muted transition-colors disabled:opacity-40"
            >
              ask claude
            </button>
          )}
        </div>

        {s ? (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-y-2 mb-4">
              <Cell label="Spot" value={fmt(s.nifty_spot)} />
              <Cell label="Futures" value={fmt(s.nifty_fut_ltp)} />
              <Cell label="Premium" value={fmt(s.fut_premium)} tone={s.fut_premium > 0 ? "bull" : "bear"} />
              <Cell label="Supertrend" value={s.supertrend_direction?.toUpperCase()} tone={stTone} />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-y-2 mb-4">
              <Cell label="VWAP" value={fmt(s.vwap)} />
              <Cell label="Spot−VWAP" value={fmt(s.spot_vs_vwap_pct)} suffix="%" tone={vwapTone} />
              <Cell label="RSI 14" value={fmt(s.rsi_14, 1)} />
              <Cell label="ST Val" value={fmt(s.supertrend_value)} />
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-y-2 mb-4">
              <Cell label="EMA 21" value={fmt(s.ema_21)} />
              <Cell label="EMA 50" value={fmt(s.ema_50)} />
              <Cell label="21−50 Δ" value={fmt(s.ema21_vs_ema50_pct, 3)} suffix="%" tone={emaTone} />
              <Cell label="ATM" value={s.option_chain?.[Math.floor((s.option_chain?.length || 1) / 2)]?.strike} />
            </div>

            {s.option_chain && s.option_chain.length > 0 && (
              <div className="mt-4">
                <div className="text-[10px] uppercase tracking-widest text-muted mb-2 border-b border-border pb-1">
                  Option chain · ATM ± 3
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs numeric">
                    <thead className="text-muted">
                      <tr className="border-b border-border">
                        <th className="text-right px-2 py-1.5">CE OI</th>
                        <th className="text-right px-2 py-1.5">CE LTP</th>
                        <th className="text-center px-2 py-1.5 text-accent">Strike</th>
                        <th className="text-left px-2 py-1.5">PE LTP</th>
                        <th className="text-left px-2 py-1.5">PE OI</th>
                      </tr>
                    </thead>
                    <tbody>
                      {s.option_chain.map((row, i) => {
                        const isAtm = i === Math.floor(s.option_chain.length / 2);
                        return (
                          <tr
                            key={row.strike}
                            className={`border-b border-border/40 ${isAtm ? "bg-accent/5" : ""}`}
                          >
                            <td className="text-right px-2 py-1">
                              {row.ce_oi ? (row.ce_oi / 100000).toFixed(1) + "L" : "—"}
                            </td>
                            <td className="text-right px-2 py-1">{fmt(row.ce_ltp)}</td>
                            <td className={`text-center px-2 py-1 ${isAtm ? "text-accent" : ""}`}>
                              {row.strike}
                            </td>
                            <td className="text-left px-2 py-1">{fmt(row.pe_ltp)}</td>
                            <td className="text-left px-2 py-1">
                              {row.pe_oi ? (row.pe_oi / 100000).toFixed(1) + "L" : "—"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-12 text-muted text-xs numeric uppercase tracking-widest">
            ─── no snapshot ───
            <div className="mt-2 text-[10px] normal-case tracking-normal">
              take a snapshot to capture current market state
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
