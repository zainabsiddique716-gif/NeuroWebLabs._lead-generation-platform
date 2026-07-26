import { useEffect, useState } from "react";
import { api } from "../api";
import type { Lead } from "../types";
import { StatusBadge } from "./StatusBadge";
import { PipelineTrack } from "./PipelineTrack";

const FILTERS = ["all", "new", "qualified", "rejected", "contacted", "replied"];

export function LeadsTable({ refreshKey }: { refreshKey: number }) {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filter, setFilter] = useState("all");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editEmail, setEditEmail] = useState("");
  const [sendingId, setSendingId] = useState<number | null>(null);
  const [sendResult, setSendResult] = useState<Record<number, string>>({});

  async function load() {
    const res = await api.listLeads();
    setLeads(res.leads);
  }

  useEffect(() => {
    load();
  }, [refreshKey]);

  const visible = filter === "all" ? leads : leads.filter((l) => l.status === filter);

  async function saveEmail(leadId: number) {
    await api.updateLead(leadId, { email: editEmail });
    setEditingId(null);
    load();
  }

  async function send(leadId: number) {
    setSendingId(leadId);
    try {
      const res = await api.sendOutreach(leadId);
      setSendResult((s) => ({ ...s, [leadId]: res.send_status }));
      load();
    } catch (e) {
      setSendResult((s) => ({ ...s, [leadId]: e instanceof Error ? e.message : "failed" }));
    } finally {
      setSendingId(null);
    }
  }

  return (
    <div>
      <PipelineTrack leads={leads} />

      <div className="flex gap-2 mb-4 flex-wrap">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-md text-xs font-mono uppercase tracking-wide transition-colors ${
              filter === f ? "bg-blue-600 text-white" : "bg-[var(--bg-panel)] text-slate-400 hover:text-slate-200"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-lg border border-[var(--border-line)]">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-slate-400 text-xs uppercase tracking-wide border-b border-[var(--border-line)]">
              <th className="px-4 py-3">Business</th>
              <th className="px-4 py-3">Email</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Reason</th>
              <th className="px-4 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((lead) => (
              <tr key={lead.id} className="border-b border-[var(--border-line)] last:border-0">
                <td className="px-4 py-3">
                  <div>{lead.business_name}</div>
                  <div className="text-xs text-slate-500">{lead.category}</div>
                </td>
                <td className="px-4 py-3 font-mono text-xs">
                  {editingId === lead.id ? (
                    <div className="flex gap-2">
                      <input
                        value={editEmail}
                        onChange={(e) => setEditEmail(e.target.value)}
                        className="bg-[var(--bg-deep)] border border-blue-600 rounded px-2 py-1 text-xs w-40"
                      />
                      <button onClick={() => saveEmail(lead.id)} className="text-emerald-400">
                        save
                      </button>
                    </div>
                  ) : (
                    <span
                      onClick={() => {
                        setEditingId(lead.id);
                        setEditEmail(lead.email || "");
                      }}
                      className="cursor-pointer hover:text-blue-400"
                      title="Click to edit"
                    >
                      {lead.email || "— click to add —"}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={lead.status} />
                </td>
                <td className="px-4 py-3 text-xs text-slate-500 max-w-[200px]">{lead.rejection_reason || "—"}</td>
                <td className="px-4 py-3">
                  {lead.status === "qualified" ? (
                    <button
                      onClick={() => send(lead.id)}
                      disabled={sendingId === lead.id}
                      className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 rounded px-3 py-1.5 text-xs font-medium"
                    >
                      {sendingId === lead.id ? "Sending…" : "Send outreach"}
                    </button>
                  ) : sendResult[lead.id] ? (
                    <span className="text-xs font-mono text-slate-400">{sendResult[lead.id]}</span>
                  ) : (
                    <span className="text-xs text-slate-600">—</span>
                  )}
                </td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-slate-500 text-sm">
                  No leads here yet — run a search and scrape some emails first.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
