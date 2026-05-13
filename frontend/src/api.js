const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function req(path, opts = {}) {
  const r = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!r.ok) {
    const detail = await r.text();
    throw new Error(`${r.status}: ${detail}`);
  }
  return r.json();
}

export const api = {
  takeSnapshot: async (file, force = false) => {
    const form = new FormData();
    if (file) form.append("screenshot", file);
    const r = await fetch(
      `${API_BASE}/snapshot${force ? "?force=true" : ""}`,
      { method: "POST", body: form }
    );
    if (!r.ok) throw new Error(await r.text());
    return r.json();
  },
  getSnapshot: (id) => req(`/snapshot/${id}`),
  createTrade: (payload) =>
    req("/trades", { method: "POST", body: JSON.stringify(payload) }),
  listTrades: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return req(`/trades${qs ? `?${qs}` : ""}`);
  },
  closeTrade: (id, outcome) =>
    req(`/trades/${id}/close`, {
      method: "PATCH",
      body: JSON.stringify(outcome),
    }),
  analyze: (snapshotId, includeScreenshot = true) =>
    req("/analyze", {
      method: "POST",
      body: JSON.stringify({
        snapshot_id: snapshotId,
        include_screenshot: includeScreenshot,
        past_trades_limit: 30,
      }),
    }),
};
