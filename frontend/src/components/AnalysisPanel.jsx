export default function AnalysisPanel({ analysis }) {
  return (
    <section className="border border-accent/40 bg-panel">
      <header className="border-b border-accent/40 px-4 py-2 flex items-center justify-between bg-accent/5">
        <div className="flex items-center gap-2">
          <span className="text-accent text-xs">◆</span>
          <h2 className="text-xs uppercase tracking-widest text-accent">
            Claude · similarity analysis
          </h2>
        </div>
        <span className="text-[10px] numeric text-muted uppercase tracking-wider">
          {analysis.past_trades_considered} past trades considered
        </span>
      </header>
      <div className="p-4">
        <div className="text-sm leading-relaxed whitespace-pre-wrap text-text">
          {analysis.analysis}
        </div>
      </div>
    </section>
  );
}
