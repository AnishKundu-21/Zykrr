import type {
  Ticket,
  TicketListResponse,
  TicketRequest,
} from "../types/ticket";

const BASE = "/tickets";

export async function analyzeTicket(req: TicketRequest): Promise<Ticket> {
  const res = await fetch(`${BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(
      err?.detail?.[0]?.msg ?? err?.detail ?? `Error ${res.status}`,
    );
  }
  return res.json();
}

export async function listTickets(): Promise<TicketListResponse> {
  const res = await fetch(BASE);
  if (!res.ok) throw new Error(`Error ${res.status}`);
  return res.json();
}
