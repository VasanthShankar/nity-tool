import { useEffect, useState } from "react";
import { api } from "./api";
import SnapshotPanel from "./components/SnapshotPanel.jsx";
import TradeForm from "./components/TradeForm.jsx";
import TradeList from "./components/TradeList.jsx";
import AnalysisPanel from "./components/AnalysisPanel.jsx";

export default function App() {
  const [tab, setTab] = useState("live");
  const [snapshot, setSnapshot] = useState(null);
  const [trades, setTrades] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadTrades = async () => {
    try {
      const list = await api.listTrades({ limit: 50 });
      setTrades(list);
    } catch (e) {
      setError(e.message);
    }
  };

  useEffect(() => {
    loadTrades();
  }, []);

  const handleSnapshot = async (file, force) => {
    setLoading(true);
    setError(null);
    setAnalysis(null);
    try {
      const s = await api.takeSnapshot(file, force);
      setSnapshot(s);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!snapshot) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.analyze(snapshot.id, !!snapshot.screenshot_b64);
      setAnalysis(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTradeCreate = async (payload) => {
    setLoading(true);
    setError(null);
    try {
      await api.createTrade({ ...payload, snapshot_id: snapshot.id });
      await loadTrades();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTradeClose = async (tradeId, outcome) => {
    try {
      await api.closeTrade(tradeId, outcome);
      await loadTrades();
    } catch (e) {
      setError(e.message);
    }
  };

  const now = new Date().toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    hour12: false,
  });

  return (
    <div className="min-h-screen bg-bg text-text">
      {/* Header */}
      <header className="border-b border-border bg-panel">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-baseline gap-3">
            <span className="text-accent text-xs numeric tracking-widest">
              ◢◤
            </span>
            <h1 className="font-display font-bold text-lg tracking-tight">
              NIFTY <span className="text-muted font-normal">/ JOURNAL</span>
            </h1>
            <span className="hidden sm:inline text-xs numeric text-muted ml-4">
              {now} IST
            </span>
          </div>
          <nav className="flex gap-1 text-xs uppercase tracking-wider">
            {["live", "history"].map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`px-3 py-1.5 border ${
                  tab === t
                    ? "border-accent text-accent bg-accent/5"
                    : "border-border text-muted hover:text-text"
                } transition-colors`}
              >
                {t}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {error && (
        <div className="max-w-7xl mx-auto px-4 mt-3">
          <div className="border border-bear/40 bg-bear/5 text-bear text-xs numeric px-3 py-2">
            ERR — {error}
          </div>
        </div>
      )}

      <main className="max-w-7xl mx-auto px-4 py-6">
        {tab === "live" ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 space-y-4">
              <SnapshotPanel
                snapshot={snapshot}
                loading={loading}
                onCapture={handleSnapshot}
                onAnalyze={handleAnalyze}
              />
              {analysis && <AnalysisPanel analysis={analysis} />}
            </div>
            <div>
              {snapshot && (
                <TradeForm
                  snapshot={snapshot}
                  onSubmit={handleTradeCreate}
                  disabled={loading}
                />
              )}
            </div>
          </div>
        ) : (
          <TradeList trades={trades} onClose={handleTradeClose} />
        )}
      </main>

      <footer className="border-t border-border mt-12">
        <div className="max-w-7xl mx-auto px-4 py-3 text-xs numeric text-muted flex justify-between">
          <span>discretionary journal · personal use</span>
          <span>v0.1</span>
        </div>
      </footer>
    </div>
  );
}
