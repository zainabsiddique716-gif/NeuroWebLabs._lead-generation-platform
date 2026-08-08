import { useEffect, useState } from "react";
import { SearchPanel } from "./components/SearchPanel";
import { LeadsTable } from "./components/LeadsTable";
import { OutreachLogView } from "./components/OutreachLogView";

type Tab = "search" | "leads" | "outreach";
type Theme = "dark" | "light";

const TABS: { key: Tab; label: string }[] = [
  { key: "search", label: "Search" },
  { key: "leads", label: "Leads" },
  { key: "outreach", label: "Outreach Log" },
];

function SunIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>("search");
  const [refreshKey, setRefreshKey] = useState(0);
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem("theme") as Theme) || "dark");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  return (
    <div className="min-h-screen bg-[var(--bg-deep)] text-slate-200">
      <header className="border-b border-[var(--border-line)] px-8 py-6 flex items-start justify-between">
        <div>
          <h1 className="font-display text-2xl font-semibold tracking-tight text-slate-50">
            Local Lead Generation
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Search → scrape → qualify → review → send — one pipeline, one dashboard.
          </p>
        </div>
        <button
          onClick={() => setTheme((t) => (t === "dark" ? "light" : "dark"))}
          className="p-2 rounded-lg bg-[var(--bg-panel)] border border-[var(--border-line)] text-slate-400 hover:text-slate-200 transition-colors"
          title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
        >
          {theme === "dark" ? <SunIcon /> : <MoonIcon />}
        </button>
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
