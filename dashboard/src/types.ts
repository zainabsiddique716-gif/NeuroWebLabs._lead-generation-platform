export interface Business {
  id: number;
  name: string;
  category: string | null;
  address: string | null;
  phone: string | null;
  rating: number | null;
  website_url: string | null;
  latitude: number | null;
  longitude: number | null;
  source: string;
}

export type LeadStatus = "new" | "qualified" | "rejected" | "contacted" | "replied";

export interface Lead {
  id: number;
  business_id: number;
  business_name: string | null;
  category: string | null;
  website_url: string | null;
  phone: string | null;
  address: string | null;
  email: string | null;
  email_found: boolean;
  website_live: boolean | null;
  status: LeadStatus;
  rejection_reason: string | null;
  updated_at: string | null;
}

export interface OutreachLogEntry {
  id: number;
  lead_id: number;
  business_name: string | null;
  channel: string;
  status: string;
  error_message: string | null;
  sent_at: string;
}
