import type { LeadStatus } from "../types";

const STYLES: Record<string, string> = {
  new: "bg-slate-700 text-slate-200",
  qualified: "bg-emerald-900 text-emerald-300 border border-emerald-700",
  rejected: "bg-rose-950 text-rose-400 border border-rose-800",
  contacted: "bg-blue-950 text-blue-300 border border-blue-700",
  replied: "bg-violet-950 text-violet-300 border border-violet-700",
};

export function StatusBadge({ status }: { status: LeadStatus | string }) {
  const style = STYLES[status] || STYLES.new;
  return (
    <span className={`px-2.5 py-1 rounded-md text-xs font-mono uppercase tracking-wide ${style}`}>
      {status}
    </span>
  );
}
