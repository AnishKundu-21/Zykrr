import React, { useState } from "react";
import type { Ticket, TicketRequest } from "../types/ticket";
import { analyzeTicket } from "../api/tickets";

interface Props {
  onSuccess: (ticket: Ticket) => void;
}

const PRIORITY_COLOR: Record<string, string> = {
  P0: "badge badge-p0",
  P1: "badge badge-p1",
  P2: "badge badge-p2",
  P3: "badge badge-p3",
};

const CATEGORY_COLOR: Record<string, string> = {
  Billing: "badge badge-billing",
  Technical: "badge badge-technical",
  Account: "badge badge-account",
  "Feature Request": "badge badge-feature",
  Other: "badge badge-other",
};

export default function TicketForm({ onSuccess }: Props) {
  const [subject, setSubject] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<Ticket | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      const req: TicketRequest = {
        subject: subject.trim(),
        description: description.trim(),
      };
      const ticket = await analyzeTicket(req);
      setResult(ticket);
      onSuccess(ticket);
      setSubject("");
      setDescription("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  const descLen = description.length;
  const descMax = 5000;

  return (
    <section className="card">
      <div className="card-header">
        <div className="card-icon card-icon--blue">
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
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
          </svg>
        </div>
        <div>
          <h2>New Ticket</h2>
          <p className="card-subtitle">
            Describe your issue and get instant AI-powered triage
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="subject">Subject</label>
          <input
            id="subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="e.g. Cannot process payment on checkout"
            required
            maxLength={300}
            disabled={loading}
          />
        </div>
        <div className="field">
          <label htmlFor="description">
            Description
            <span
              className={`char-count ${descLen > descMax * 0.9 ? "char-count--warn" : ""}`}
            >
              {descLen.toLocaleString()} / {descMax.toLocaleString()}
            </span>
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Provide full details — what happened, steps to reproduce, any error messages…"
            required
            rows={5}
            maxLength={descMax}
            disabled={loading}
          />
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

        <button
          type="submit"
          className="btn-primary"
          disabled={loading || !subject.trim() || !description.trim()}
        >
          {loading ? (
            <>
              <span className="spinner" />
              Analyzing…
            </>
          ) : (
            <>
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
              Analyze &amp; Submit
            </>
          )}
        </button>
      </form>

      {result && (
        <div className="result-panel">
          <div className="result-header">
            <div className="result-header-icon">
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
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h3>Analysis Complete</h3>
          </div>

          <div className="result-grid">
            <div className="result-item">
              <span className="result-label">Category</span>
              <span
                className={
                  CATEGORY_COLOR[result.category] ?? "badge badge-other"
                }
              >
                {result.category}
              </span>
            </div>
            <div className="result-item">
              <span className="result-label">Priority</span>
              <span className={PRIORITY_COLOR[result.priority] ?? "badge"}>
                {result.priority}
              </span>
            </div>
            <div className="result-item">
              <span className="result-label">Urgency</span>
              <span
                className={`badge ${result.urgency ? "badge-urgent" : "badge-normal"}`}
              >
                {result.urgency ? "Urgent" : "Normal"}
              </span>
            </div>
            <div className="result-item">
              <span className="result-label">Confidence</span>
              <div className="confidence-bar-wrapper">
                <div
                  className="confidence-bar"
                  style={{ width: `${Math.round(result.confidence * 100)}%` }}
                />
                <span className="confidence-pct">
                  {Math.round(result.confidence * 100)}%
                </span>
              </div>
            </div>
          </div>

          {result.keywords.length > 0 && (
            <div className="tags-row">
              <span className="result-label">Keywords</span>
              {result.keywords.map((kw) => (
                <span key={kw} className="tag">
                  {kw}
                </span>
              ))}
            </div>
          )}

          {result.custom_flags.length > 0 && (
            <div className="tags-row">
              <span className="result-label">Flags</span>
              {result.custom_flags.map((f) => (
                <span key={f} className="tag tag-flag">
                  {f.replace(/_/g, " ")}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
