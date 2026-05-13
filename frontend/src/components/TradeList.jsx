import { useState } from "react";

function fmt(n, d = 2) {
  if (n === null || n === undefined) return "—";
  return Number(n).toLocaleString("en-IN", {
    minimumFractionDigits: d,
    maximumFractionDigits: d,
  });
}

function CloseForm({ trade, onClose, onCancel }) {
  const [exitPrice, setExitPrice] = useState("");
  const [pnl, setPnl] = useState("");
  const [mfe, setMfe] = useState("");
  const [mae, setMae] = useState("");
  const [exitReason, setExitReason] = useState("");

  const submit = (e) => {
    e.preventDefault();
    onClose(trade.id, {
      exit_price: parseFloat(exitPrice),
      pnl: parseFloat(pnl),
      mfe: mfe ? parseFloat(mfe) : null,
      mae: mae ? parseFloat(mae) : null,
      exit_reason: exitReason || null,
    });
  };

  return (
    <form onSubmit={submit} className="mt-3 p-3 border border-border bg-bg space-y-2">
      <div className="grid grid-cols-2 gap-2">
        <input
          required
          type="number"
          step="0.05"
          placeholder="Exit price"
          value={exitPrice}
          onChange={(e) => setExitPrice(e.target.value)}
          className="bg-panel border border-border px-2 py-1 text-xs numeric"
        />
        <input
          required
          type="number"
          step="0.01"
          placeholder="Net P&L"
          value={pnl}
          onChange={(e) => setPnl(e.target.value)}
          className="bg-panel border border-border px-2 py-1 text-xs numeric"
        />
        <input
          type="number"
          step="0.05"
          placeholder="MFE"
          value={mfe}
          onChange={(e) => setMfe(e.target.value)}
          className="bg-panel border border-border px-2 py-1 text-xs numeric"
        />
        <input
          type="number"
          step="0.05"
          placeholder="MAE"
          value={mae}
          onChange={(e) => setMae(e.target.value)}
          className="bg-panel border border-border px-2 py-1 text-xs numeric"
        />
      </div>
      <input
        type="text"
        placeholder="Exit reason"
        value={exitReason}
        onChange={(e) => setExitReason(e.target.value)}
        className="w-full bg-panel border border-border px-2 py-1 text-xs"
      />
      <div className="flex gap-2">
        <button
          type="submit"
          className="flex-1 text-xs numeric uppercase tracking-wider py-1.5 border border-accent text-accent hover:bg-accent/10"
        >
          ▸ Close trade
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 text-xs numeric uppercase tracking-wider py-1.5 border border-border text-muted hover:text-text"
        >
          cancel
        </button>
      </div>
    </form>
  );
}

export default function TradeList({ trades, onClose }) {
  const [closingId, setClosingId] = useState(null);

  if (!trades.length) {
    return (
      <div className="text-center py-16 text-muted text-xs numeric uppercase tracking-widest">
        ─── no trades yet ───
      </div>
    );
  }

  // Summary stats
  const closed = trades.filter((t) => t.closed && t.pnl != null);
  const wins = closed.filter((t) => t.pnl > 0);
  const totalPnl = closed.reduce((s, t) => s + (t.pnl || 0), 0);
  const winRate = closed.length ? (wins.length / closed.length) * 100 : 0;

  return (
    <div className="space-y-4">
      {/* Stats strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 border border-border bg-panel">
        <div className="px-4 py-3 border-r border-border">
          <div className="text-[10px] uppercase tracking-widest text-muted">Trades</div>
          <div className="text-2xl font-display font-bold numeric mt-1">{trades.length}</div>
        </div>
        <div className="px-4 py-3 border-r border-border">
          <div className="text-[10px] uppercase tracking-widest text-muted">Closed</div>
          <div className="text-2xl font-display font-bold numeric mt-1">{closed.length}</div>
        </div>
        <div className="px-4 py-3 border-r border-border">
          <div className="text-[10px] uppercase tracking-widest text-muted">Win rate</div>
          <div className="text-2xl font-display font-bold numeric mt-1">
            {winRate.toFixed(0)}<span className="text-sm text-muted">%</span>
          </div>
        </div>
        <div className="px-4 py-3">
          <div className="text-[10px] uppercase tracking-widest text-muted">Net P&L</div>
          <div
            className={`text-2xl font-display font-bold numeric mt-1 ${
              totalPnl > 0 ? "text-bull" : totalPnl < 0 ? "text-bear" : ""
            }`}
          >
            {fmt(totalPnl)}
          </div>
        </div>
      </div>

      {/* Rows */}
      <div className="border border-border bg-panel">
        {trades.map((t, i) => (
          <article
            key={t.id}
            className={`p-4 ${i !== trades.length - 1 ? "border-b border-border" : ""}`}
          >
            <header className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <span className="text-xs numeric text-muted">
                  #{t.id} · {new Date(t.created_at).toLocaleString("en-IN", { hour12: false, timeZone: "Asia/Kolkata" })}
                </span>
                <span
                  className={`text-[10px] numeric uppercase tracking-widest px-2 py-0.5 border ${
                    t.action === "entered"
                      ? "border-bull/40 text-bull"
                      : "border-muted text-muted"
                  }`}
                >
                  {t.action}
                </span>
                {t.setup_tag && (
                  <span className="text-[10px] numeric uppercase tracking-widest px-2 py-0.5 border border-border text-muted">
                    {t.setup_tag}
                  </span>
                )}
              </div>
              {t.closed && t.pnl != null && (
                <span
                  className={`numeric text-lg font-display font-bold ${
                    t.pnl > 0 ? "text-bull" : "text-bear"
                  }`}
                >
                  {t.pnl > 0 ? "+" : ""}{fmt(t.pnl)}
                </span>
              )}
            </header>

            {t.action === "entered" && (
              <div className="text-xs numeric text-muted mb-2">
                {t.direction?.toUpperCase()} · {t.strike} {t.option_type} @ {fmt(t.entry_price)}
                {t.quantity ? ` · ${t.quantity} lot${t.quantity > 1 ? "s" : ""}` : ""}
                {t.exit_price != null && <> → exit {fmt(t.exit_price)}</>}
              </div>
            )}

            <p className="text-sm text-text leading-relaxed">{t.reasoning}</p>

            {t.action === "entered" && !t.closed && (
              <>
                {closingId === t.id ? (
                  <CloseForm
                    trade={t}
                    onClose={(id, outcome) => {
                      onClose(id, outcome);
                      setClosingId(null);
                    }}
                    onCancel={() => setClosingId(null)}
                  />
                ) : (
                  <button
                    onClick={() => setClosingId(t.id)}
                    className="mt-2 text-xs numeric uppercase tracking-wider px-3 py-1 border border-border text-muted hover:text-text hover:border-muted"
                  >
                    + log outcome
                  </button>
                )}
              </>
            )}

            {t.closed && t.exit_reason && (
              <div className="mt-2 text-xs numeric text-muted">
                exit: {t.exit_reason}
              </div>
            )}
          </article>
        ))}
      </div>
    </div>
  );
}
