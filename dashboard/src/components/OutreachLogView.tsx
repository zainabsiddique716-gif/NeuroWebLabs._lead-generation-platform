import { useEffect, useState } from "react";
import { api } from "../api";
import type { OutreachLogEntry } from "../types";

export function OutreachLogView({ refreshKey }: { refreshKey: number }) {
  const [logs, setLogs] = useState<OutreachLogEntry[]>([]);

  useEffect(() => {
    api.listOutreachLogs().then((res) => setLogs(res.logs));
  }, [refreshKey]);

  return (
    <div className="overflow-x-auto rounded-lg border border-[var(--border-line)]">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-400 text-xs uppercase tracking-wide border-b border-[var(--border-line)]">
            <th className="px-4 py-3">Business</th>
            <th className="px-4 py-3">Channel</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Sent at</th>
            <th className="px-4 py-3">Error</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id} className="border-b border-[var(--border-line)] last:border-0">
              <td className="px-4 py-3">{log.business_name}</td>
              <td className="px-4 py-3 text-slate-400">{log.channel}</td>
              <td className="px-4 py-3">
                <span
                  className={`font-mono text-xs uppercase px-2 py-1 rounded ${
                    log.status === "sent"
                      ? "bg-emerald-900 text-emerald-300"
                      : log.status === "dry_run"
                      ? "bg-amber-900 text-amber-300"
                      : "bg-rose-950 text-rose-400"
                  }`}
                >
                  {log.status}
                </span>
              </td>
              <td className="px-4 py-3 text-xs text-slate-500 font-mono">
                {new Date(log.sent_at).toLocaleString()}
              </td>
              <td className="px-4 py-3 text-xs text-rose-400">{log.error_message || "—"}</td>
            </tr>
          ))}
          {logs.length === 0 && (
            <tr>
              <td colSpan={5} className="px-4 py-8 text-center text-slate-500 text-sm">
                No outreach sent yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
