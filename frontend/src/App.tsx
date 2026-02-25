import { useCallback, useEffect, useState } from "react";
import type { Ticket } from "./types/ticket";
import { listTickets } from "./api/tickets";
import TicketForm from "./components/TicketForm";
import TicketList from "./components/TicketList";
import "./index.css";

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [listError, setListError] = useState<string | null>(null);

  const fetchTickets = useCallback(async () => {
    setListLoading(true);
    setListError(null);
    try {
      const data = await listTickets();
      setTickets(data.tickets);
    } catch (err: unknown) {
      setListError(
        err instanceof Error ? err.message : "Failed to load tickets",
      );
    } finally {
      setListLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  function handleNewTicket(ticket: Ticket) {
    setTickets((prev) => [ticket, ...prev]);
  }

  const stats = {
    total: tickets.length,
    critical: tickets.filter((t) => t.priority === "P0").length,
    urgent: tickets.filter((t) => t.urgency).length,
  };

  return (
    <div className="app">
      <div className="header-accent" />
      <header className="app-header">
        <div className="header-inner">
          <div className="header-brand">
            <div className="brand-icon">
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
            <div>
              <h1>AI Ticket Triage</h1>
              <p className="subtitle">
                Intelligent support ticket classification
              </p>
            </div>
          </div>
          {tickets.length > 0 && (
            <div className="header-stats">
              <div className="stat-chip">
                <span className="stat-value">{stats.total}</span>
                <span className="stat-label">Tickets</span>
              </div>
              <div className="stat-chip stat-chip--danger">
                <span className="stat-value">{stats.critical}</span>
                <span className="stat-label">Critical</span>
              </div>
              <div className="stat-chip stat-chip--warning">
                <span className="stat-value">{stats.urgent}</span>
                <span className="stat-label">Urgent</span>
              </div>
            </div>
          )}
        </div>
      </header>
      <main className="app-main">
        <TicketForm onSuccess={handleNewTicket} />
        <TicketList tickets={tickets} loading={listLoading} error={listError} />
      </main>
      <footer className="app-footer">
        <p>
          AI Ticket Triage &middot; Heuristic NLP Engine &middot; Built with
          FastAPI &amp; React
        </p>
      </footer>
    </div>
  );
}
