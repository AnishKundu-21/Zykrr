export interface Ticket {
  id: number;
  subject: string;
  description: string;
  category: string;
  priority: "P0" | "P1" | "P2" | "P3";
  urgency: boolean;
  confidence: number;
  keywords: string[];
  custom_flags: string[];
  created_at: string;
}

export interface TicketListResponse {
  tickets: Ticket[];
  total: number;
}

export interface TicketRequest {
  subject: string;
  description: string;
}
