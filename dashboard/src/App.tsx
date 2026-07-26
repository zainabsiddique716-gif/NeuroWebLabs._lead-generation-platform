import { useState } from "react";
import { SearchPanel } from "./components/SearchPanel";
import { LeadsTable } from "./components/LeadsTable";
import { OutreachLogView } from "./components/OutreachLogView";

type Tab = "search" | "leads" | "outreach";

const TABS: { key: Tab; label: string }[] = [
  { key: "search", label: "Search" },
  { key: "leads", label: "Leads" },
  { key: "outreach", label: "Outreach Log" },
];

export default function App() {
  const [tab, setTab] = useState<Tab>("search");
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="min-h-screen bg-[var(--bg-deep)] text-slate-200">
      <header className="border-b border-[var(--border-line)] px-8 py-6">
        <h1 className="font-display text-2xl font-semibold tracking-tight text-slate-50">
          Local Lead Generation
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Search → scrape → qualify → review → send — one pipeline, one dashboard.
        </p>
      </header>

      <nav className="px-8 pt-6 flex gap-1 border-b border-[var(--border-line)]">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium rounded-t-lg transition-colors ${
              tab === t.key
                ? "bg-[var(--bg-panel)] text-slate-50 border-x border-t border-[var(--border-line)]"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="p-8 max-w-6xl mx-auto">
        {tab === "search" && <SearchPanel onLeadUpdated={() => setRefreshKey((k) => k + 1)} />}
        {tab === "leads" && <LeadsTable refreshKey={refreshKey} />}
        {tab === "outreach" && <OutreachLogView refreshKey={refreshKey} />}
      </main>
    </div>
  );
}
