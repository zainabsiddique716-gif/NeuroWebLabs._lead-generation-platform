import type { Lead } from "../types";

const STAGES: { key: string; label: string; dot: string }[] = [
  { key: "new", label: "New", dot: "bg-slate-400" },
  { key: "qualified", label: "Qualified", dot: "bg-emerald-400" },
  { key: "rejected", label: "Rejected", dot: "bg-rose-500" },
  { key: "contacted", label: "Contacted", dot: "bg-blue-400" },
  { key: "replied", label: "Replied", dot: "bg-violet-400" },
];

export function PipelineTrack({ leads }: { leads: Lead[] }) {
  const counts = STAGES.map((s) => leads.filter((l) => l.status === s.key).length);

  return (
    <div className="relative py-6 px-2">
      <div className="absolute left-4 right-4 top-[42px] h-px bg-[var(--border-line)]" />
      <div className="flex justify-between relative">
        {STAGES.map((stage, i) => (
          <div key={stage.key} className="flex flex-col items-center gap-2 flex-1">
            <span className="font-mono text-2xl font-medium text-slate-100">
              {String(counts[i]).padStart(2, "0")}
            </span>
            <div className={`w-2.5 h-2.5 rounded-full ${stage.dot} ring-4 ring-[var(--bg-deep)]`} />
            <span className="text-[11px] uppercase tracking-widest text-slate-400">{stage.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
