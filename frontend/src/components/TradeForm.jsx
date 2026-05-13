import { useState } from "react";

const Input = ({ label, ...props }) => (
  <label className="block">
    <span className="text-[10px] uppercase tracking-widest text-muted">
      {label}
    </span>
    <input
      {...props}
      className="w-full mt-1 bg-bg border border-border px-2 py-1.5 text-sm numeric focus:border-accent focus:outline-none"
    />
  </label>
);

const Select = ({ label, options, ...props }) => (
  <label className="block">
    <span className="text-[10px] uppercase tracking-widest text-muted">
      {label}
    </span>
    <select
      {...props}
      className="w-full mt-1 bg-bg border border-border px-2 py-1.5 text-sm numeric focus:border-accent focus:outline-none"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  </label>
);

export default function TradeForm({ snapshot, onSubmit, disabled }) {
  const [action, setAction] = useState("entered");
  const [direction, setDirection] = useState("bullish");
  const [strike, setStrike] = useState(
    snapshot?.option_chain?.[Math.floor((snapshot?.option_chain?.length || 1) / 2)]?.strike || ""
  );
  const [optionType, setOptionType] = useState("CE");
  const [entryPrice, setEntryPrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [setupTag, setSetupTag] = useState("");
  const [reasoning, setReasoning] = useState("");

  const submit = (e) => {
    e.preventDefault();
    if (!reasoning.trim()) {
      alert("Reasoning is required — this is the whole point of the journal");
      return;
    }
    onSubmit({
      action,
      direction: action === "entered" ? direction : null,
      strike: action === "entered" && strike ? parseInt(strike) : null,
      option_type: action === "entered" ? optionType : null,
      entry_price: action === "entered" && entryPrice ? parseFloat(entryPrice) : null,
      quantity: action === "entered" && quantity ? parseInt(quantity) : null,
      setup_tag: setupTag || null,
      reasoning,
    });
    // Reset
    setEntryPrice("");
    setQuantity("");
    setSetupTag("");
    setReasoning("");
  };

  return (
    <section className="border border-border bg-panel">
      <header className="border-b border-border px-4 py-2">
        <h2 className="text-xs uppercase tracking-widest text-muted">
          Log decision
        </h2>
      </header>

      <form onSubmit={submit} className="p-4 space-y-3">
        <div className="flex gap-1">
          {[
            ["entered", "Entered"],
            ["skipped", "Skipped"],
          ].map(([v, l]) => (
            <button
              key={v}
              type="button"
              onClick={() => setAction(v)}
              className={`flex-1 text-xs numeric uppercase tracking-wider py-1.5 border transition-colors ${
                action === v
                  ? v === "entered"
                    ? "border-bull text-bull bg-bull/5"
                    : "border-muted text-text bg-panel2"
                  : "border-border text-muted"
              }`}
            >
              {l}
            </button>
          ))}
        </div>

        {action === "entered" && (
          <>
            <Select
              label="Direction"
              value={direction}
              onChange={(e) => setDirection(e.target.value)}
              options={[
                { value: "bullish", label: "Bullish" },
                { value: "bearish", label: "Bearish" },
                { value: "neutral", label: "Neutral" },
              ]}
            />
            <div className="grid grid-cols-2 gap-2">
              <Input
                label="Strike"
                type="number"
                step="50"
                value={strike}
                onChange={(e) => setStrike(e.target.value)}
              />
              <Select
                label="Type"
                value={optionType}
                onChange={(e) => setOptionType(e.target.value)}
                options={[
                  { value: "CE", label: "CE (Call)" },
                  { value: "PE", label: "PE (Put)" },
                ]}
              />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Input
                label="Entry price"
                type="number"
                step="0.05"
                value={entryPrice}
                onChange={(e) => setEntryPrice(e.target.value)}
              />
              <Input
                label="Lots"
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
              />
            </div>
          </>
        )}

        <Input
          label="Setup tag"
          type="text"
          placeholder="e.g. vwap_reversion"
          value={setupTag}
          onChange={(e) => setSetupTag(e.target.value)}
        />

        <label className="block">
          <span className="text-[10px] uppercase tracking-widest text-muted">
            Reasoning <span className="text-bear">*</span>
          </span>
          <textarea
            value={reasoning}
            onChange={(e) => setReasoning(e.target.value)}
            rows={5}
            placeholder="Why this trade / why skipped. Be specific — your future self will thank you."
            className="w-full mt-1 bg-bg border border-border px-2 py-1.5 text-sm focus:border-accent focus:outline-none resize-none"
          />
        </label>

        <button
          type="submit"
          disabled={disabled}
          className="w-full text-xs numeric uppercase tracking-wider py-2 border border-accent text-accent hover:bg-accent/10 transition-colors disabled:opacity-40"
        >
          ▸ Save
        </button>
      </form>
    </section>
  );
}
