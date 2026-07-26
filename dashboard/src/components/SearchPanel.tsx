import { useState } from "react";
import { api } from "../api";
import type { Business } from "../types";

export function SearchPanel({ onLeadUpdated }: { onLeadUpdated: () => void }) {
  const [query, setQuery] = useState("dentists");
  const [location, setLocation] = useState("Lahore, Pakistan");
  const [loading, setLoading] = useState(false);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [scraping, setScraping] = useState<Record<number, string>>({});
  const [error, setError] = useState<string | null>(null);

  async function runSearch() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.search(query, location);
      setBusinesses(res.businesses);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function scrape(businessId: number) {
    setScraping((s) => ({ ...s, [businessId]: "Scraping..." }));
    try {
      const res = await api.scrapeAndQualify(businessId);
      const lead = res.lead;
      const label = lead.email_found
        ? `${lead.email} → ${lead.status}`
        : `not found (${res.scrape_error_reason ?? "no_email_found"})`;
      setScraping((s) => ({ ...s, [businessId]: label }));
      onLeadUpdated();
    } catch (e) {
      setScraping((s) => ({ ...s, [businessId]: "error" }));
    }
  }

  return (
    <div>
      <div className="flex flex-wrap gap-3 mb-6">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. dentists, gyms"
          className="bg-[var(--bg-panel)] border border-[var(--border-line)] rounded-lg px-4 py-2.5 text-sm flex-1 min-w-[180px] focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          placeholder="e.g. Lahore, Pakistan"
          className="bg-[var(--bg-panel)] border border-[var(--border-line)] rounded-lg px-4 py-2.5 text-sm flex-1 min-w-[180px] focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={runSearch}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-400 rounded-lg px-6 py-2.5 text-sm font-medium transition-colors"
        >
          {loading ? "Searching…" : "Run search"}
        </button>
      </div>

      {error && <p className="text-rose-400 text-sm mb-4">{error}</p>}

      {businesses.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-[var(--border-line)]">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-400 text-xs uppercase tracking-wide border-b border-[var(--border-line)]">
                <th className="px-4 py-3">Business</th>
                <th className="px-4 py-3">Address</th>
                <th className="px-4 py-3">Website</th>
                <th className="px-4 py-3">Email</th>
              </tr>
            </thead>
            <tbody>
              {businesses.map((b) => (
                <tr key={b.id} className="border-b border-[var(--border-line)] last:border-0">
                  <td className="px-4 py-3">{b.name}</td>
                  <td className="px-4 py-3 text-slate-400">{b.address || "—"}</td>
                  <td className="px-4 py-3">
                    {b.website_url ? (
                      <a href={b.website_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">
                        visit
                      </a>
                    ) : (
                      <span className="text-slate-500">none</span>
                    )}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {scraping[b.id] ? (
                      <span className="text-slate-300">{scraping[b.id]}</span>
                    ) : b.website_url ? (
                      <button
                        onClick={() => scrape(b.id)}
                        className="bg-[var(--border-line)] hover:bg-blue-900 rounded px-3 py-1.5 text-xs font-sans"
                      >
                        Scrape email
                      </button>
                    ) : (
                      <span className="text-slate-500">no website</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
