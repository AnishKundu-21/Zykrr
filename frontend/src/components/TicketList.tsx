import { useState } from "react";
import type { Ticket } from "../types/ticket";

interface Props {
  tickets: Ticket[];
  loading: boolean;
  error: string | null;
}

const PRIORITY_LABEL: Record<string, string> = {
  P0: "Critical",
  P1: "High",
  P2: "Medium",
  P3: "Low",
};

const PRIORITY_CLASS: Record<string, string> = {
  P0: "badge badge-p0",
  P1: "badge badge-p1",
  P2: "badge badge-p2",
  P3: "badge badge-p3",
};

const CATEGORY_CLASS: Record<string, string> = {
  Billing: "badge badge-billing",
  Technical: "badge badge-technical",
  Account: "badge badge-account",
  "Feature Request": "badge badge-feature",
  Other: "badge badge-other",
};

function formatDate(iso: string) {
  return new Date(iso).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: true,
  });
}

function timeAgo(iso: string) {
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function TicketList({ tickets, loading, error }: Props) {
  const [selected, setSelected] = useState<Ticket | null>(null);

  return (
    <>
      {/* ── Modal ────────────────────────────────────── */}
      {selected && (
        <div className="modal-backdrop" onClick={() => setSelected(null)}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header-strip">
              <span className={PRIORITY_CLASS[selected.priority] ?? "badge"}>
                {selected.priority} &middot;{" "}
                {PRIORITY_LABEL[selected.priority] ?? selected.priority}
              </span>
              <span
                className={`badge ${selected.urgency ? "badge-urgent" : "badge-normal"}`}
              >
                {selected.urgency ? "Urgent" : "Normal"}
              </span>
              <span className="modal-id">#{selected.id}</span>
              <button
                className="modal-close"
                onClick={() => setSelected(null)}
                aria-label="Close"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            <h2 className="modal-title">{selected.subject}</h2>
            <p className="modal-description">{selected.description}</p>

            <div className="modal-grid">
              <div className="modal-field">
                <span className="result-label">Category</span>
                <span
                  className={
                    CATEGORY_CLASS[selected.category] ?? "badge badge-other"
                  }
                >
                  {selected.category}
                </span>
              </div>
              <div className="modal-field">
                <span className="result-label">Confidence</span>
                <div
                  className="confidence-bar-wrapper"
                  style={{ maxWidth: 160 }}
                >
                  <div
                    className="confidence-bar"
                    style={{
                      width: `${Math.round(selected.confidence * 100)}%`,
                    }}
                  />
                  <span className="confidence-pct">
                    {Math.round(selected.confidence * 100)}%
                  </span>
                </div>
              </div>
              <div className="modal-field">
                <span className="result-label">Submitted</span>
                <span className="modal-date">
                  {formatDate(selected.created_at)}
                </span>
              </div>
            </div>

            {selected.keywords.length > 0 && (
              <div className="tags-row">
                <span className="result-label">Keywords</span>
                {selected.keywords.map((kw) => (
                  <span key={kw} className="tag">
                    {kw}
                  </span>
                ))}
              </div>
            )}
            {selected.custom_flags.length > 0 && (
              <div className="tags-row">
                <span className="result-label">Flags</span>
                {selected.custom_flags.map((f) => (
                  <span key={f} className="tag tag-flag">
                    {f.replace(/_/g, " ")}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── Ticket List ──────────────────────────────── */}
      <section className="card">
        <div className="card-header">
          <div className="card-icon card-icon--purple">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
              <line x1="3" y1="9" x2="21" y2="9" />
              <line x1="9" y1="21" x2="9" y2="9" />
            </svg>
          </div>
          <div>
            <h2>
              Ticket History
              {tickets.length > 0 && (
                <span className="count-badge">{tickets.length}</span>
              )}
            </h2>
            <p className="card-subtitle">
              View and manage all analyzed tickets
            </p>
          </div>
        </div>

        {error && (
          <div className="error-msg">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </div>
        )}

        {loading && tickets.length === 0 && (
          <div className="empty-state">
            <div className="skeleton-row" />
            <div className="skeleton-row skeleton-row--short" />
            <div className="skeleton-row" />
          </div>
        )}

        {!loading && tickets.length === 0 && !error && (
          <div className="empty-state">
            <div className="empty-icon">
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <p className="empty-title">No tickets yet</p>
            <p className="empty-subtitle">
              Submit your first ticket above to get started
            </p>
          </div>
        )}

        {tickets.length > 0 && (
          <div className="ticket-cards">
            {tickets.map((t) => (
              <div
                key={t.id}
                className="ticket-card"
                onClick={() => setSelected(t)}
              >
                <div className="ticket-card-top">
                  <span className="ticket-card-id">#{t.id}</span>
                  <span className="ticket-card-time">
                    {timeAgo(t.created_at)}
                  </span>
                </div>
                <h3 className="ticket-card-subject">{t.subject}</h3>
                <div className="ticket-card-badges">
                  <span
                    className={
                      CATEGORY_CLASS[t.category] ?? "badge badge-other"
                    }
                  >
                    {t.category}
                  </span>
                  <span className={PRIORITY_CLASS[t.priority] ?? "badge"}>
                    {t.priority}
                  </span>
                  {t.urgency && (
                    <span className="badge badge-urgent">Urgent</span>
                  )}
                </div>
                <div className="ticket-card-bottom">
                  <div className="confidence-bar-wrapper small">
                    <div
                      className="confidence-bar"
                      style={{ width: `${Math.round(t.confidence * 100)}%` }}
                    />
                    <span className="confidence-pct">
                      {Math.round(t.confidence * 100)}%
                    </span>
                  </div>
                  {t.custom_flags.length > 0 && (
                    <div className="ticket-card-flags">
                      {t.custom_flags.map((f) => (
                        <span key={f} className="tag tag-flag">
                          {f.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
