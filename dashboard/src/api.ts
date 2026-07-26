import type { Business, Lead, OutreachLogEntry } from "./types";

const BASE_URL = "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  search: (query: string, location: string, limit = 20) =>
    request<{ search_id: number; count: number; businesses: Business[] }>("/api/search", {
      method: "POST",
      body: JSON.stringify({ query, location, limit }),
    }),

  scrapeAndQualify: (businessId: number) =>
    request<{ scrape_error_reason: string | null; lead: Lead }>(`/api/scrape/${businessId}`, {
      method: "POST",
    }),

  listLeads: (status?: string) =>
    request<{ count: number; leads: Lead[] }>(`/api/leads${status ? `?status=${status}` : ""}`),

  updateLead: (leadId: number, updates: { email?: string; status?: string }) =>
    request<Lead>(`/api/leads/${leadId}`, {
      method: "PUT",
      body: JSON.stringify(updates),
    }),

  sendOutreach: (leadId: number) =>
    request<{ send_status: string; error: string | null; lead_status: string }>(
      `/api/leads/${leadId}/send`,
      { method: "POST" }
    ),

  listOutreachLogs: () => request<{ count: number; logs: OutreachLogEntry[] }>("/api/outreach-logs"),
};
