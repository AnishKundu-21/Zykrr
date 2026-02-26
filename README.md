# AI-Powered Support Ticket Triage

**GitHub Repository:** https://github.com/AnishKundu-21/Zykrr

A full-stack application that automatically classifies and prioritises customer support tickets using a **config-driven heuristic NLP pipeline** — no external AI APIs, no paid services, no internet required.

Submit a ticket, and the system instantly returns its **category**, **priority (P0–P3)**, **urgency flag**, **confidence score**, and any triggered **custom rule flags**.

---

## Table of Contents

1. [Quick Start (Docker)](#quick-start-docker)
2. [Local Development](#local-development)
3. [Project Structure](#project-structure)
4. [Architecture & Design Decisions](#architecture--design-decisions)
5. [NLP Pipeline Explained](#nlp-pipeline-explained)
6. [Priority System](#priority-system)
7. [Custom Rules & Flags](#custom-rules--flags)
8. [API Reference](#api-reference)
9. [Data Model](#data-model)
10. [Frontend Overview](#frontend-overview)
11. [Configuration Reference](#configuration-reference)
12. [Running Tests](#running-tests)
13. [Environment & Dependencies](#environment--dependencies)

---

## Quick Start (Docker)

The entire stack (backend + frontend) runs with a single command:

```bash
git clone https://github.com/AnishKundu-21/Zykrr.git
cd Zykrr
docker-compose up --build
```

| Service      | URL                          |
|--------------|------------------------------|
| Frontend     | http://localhost             |
| Backend API  | http://localhost:8000        |
| Swagger Docs | http://localhost:8000/docs   |
| ReDoc        | http://localhost:8000/redoc  |
| Health Check | http://localhost:8000/health |

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+ or [Bun](https://bun.sh)
- Git

---

### Backend

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create the data directory for SQLite
mkdir -p data

# Start the development server (hot-reload enabled)
uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`.

---

### Frontend

Using **Bun** (recommended):

```bash
cd frontend
bun install
bun run dev          # http://localhost:5173
```

Using **npm** instead:

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

The Vite dev server is pre-configured to proxy all `/tickets` and `/health` requests to `http://localhost:8000`, so no CORS issues during development.

---

### Build for Production

```bash
# Backend: already production-ready via uvicorn
# Frontend:
cd frontend
bun run build        # outputs to frontend/dist/
```

---

## Project Structure

```
Zykrr/
├── docker-compose.yml           # Orchestrates backend + frontend containers
├── README.md
│
├── backend/
│   ├── Dockerfile               # Python 3.11-slim image, runs uvicorn
│   ├── requirements.txt         # All Python dependencies
│   ├── pytest.ini               # Pytest configuration
│   └── app/
│       ├── main.py              # FastAPI app factory, CORS, lifespan hooks
│       ├── config.py            # ALL keyword lists and rule definitions (single source of truth)
│       ├── database.py          # Async SQLAlchemy engine, session factory, Base, init_db
│       ├── models.py            # Ticket ORM model (SQLite table definition)
│       ├── schemas.py           # Pydantic request & response schemas
│       ├── controllers/
│       │   └── ticket_controller.py   # HTTP route handlers (thin — no business logic)
│       ├── services/
│       │   └── ticket_service.py      # Business logic: orchestrate analysis + DB persistence
│       ├── analyzers/
│       │   ├── classifier.py          # Category classification (keyword hit counting)
│       │   ├── priority.py            # Priority ladder + urgency + custom rule overrides
│       │   └── analyzer.py            # Orchestrator: combines classifier + priority → AnalysisResult
│       └── tests/
│           ├── test_classifier.py     # Unit tests for classification logic
│           ├── test_priority.py       # Unit tests for priority and all custom rules
│           └── test_api.py            # Integration tests for HTTP endpoints
│
└── frontend/
    ├── Dockerfile               # Node build stage → nginx serve stage
    ├── nginx.conf               # Reverse-proxy config: serves dist/, proxies /tickets + /health
    ├── vite.config.ts           # Vite config with dev-server proxy
    ├── tsconfig.json            # TypeScript strict config
    ├── package.json
    └── src/
        ├── main.tsx             # React 18 entry point (createRoot)
        ├── App.tsx              # Root component: state, layout shell, header stats
        ├── index.css            # All styles (design tokens, component styles, responsive)
        ├── api/
        │   └── tickets.ts       # Typed API client (analyzeTicket, listTickets)
        ├── types/
        │   └── ticket.ts        # TypeScript interfaces (Ticket, TicketRequest)
        └── components/
            ├── TicketForm.tsx   # Submission form with inline analysis result panel
            └── TicketList.tsx   # Card grid of past tickets + detail modal
```

---

## Architecture & Design Decisions

### Layered Architecture

The backend follows a strict **Controller → Service → Analyzer** layering:

```
HTTP Request
     │
     ▼
┌─────────────────────────────────────────────────────┐
│  Controller  (ticket_controller.py)                  │
│  • Validates input via Pydantic schemas              │
│  • Delegates entirely to the service layer           │
│  • Returns typed HTTP response                       │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  Service  (ticket_service.py)                        │
│  • Calls the analyzer pipeline                       │
│  • Persists the result to SQLite via async ORM       │
│  • Maps ORM model → Pydantic response schema         │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│  Analyzers  (analyzer.py → classifier + priority)   │
│  • Pure functions — zero I/O, zero side effects      │
│  • Fully testable in isolation                       │
│  • All logic driven by config.py keyword lists       │
└─────────────────────────────────────────────────────┘
```

**Why this separation?**
- Controllers stay thin and swappable (REST today, gRPC tomorrow).
- Services own the transaction boundary — they decide what gets persisted.
- Analyzers are pure functions: easy to unit-test, benchmark, and replace with a real ML model later without touching the service or controller.

---

### Config-Driven NLP

**All keyword lists live in `config.py` — not in the logic functions.**

This means:
- Adding a new rule = adding keywords to one file, no logic changes required.
- The system is transparent and auditable — anyone can read what triggers what.
- QA can tune keyword lists without touching Python logic.

---

### Async-First Backend

The backend uses `SQLAlchemy` with the `aiosqlite` driver and FastAPI's async request handlers. This means:
- No thread-blocking during database I/O.
- The app scales to concurrent requests without a thread pool.
- Production-ready for a swap to PostgreSQL (`asyncpg` driver) by changing one line in `config.py`.

---

## NLP Pipeline Explained

The analysis pipeline runs on every `POST /tickets/analyze` call. No external services are invoked.

### Step 1 — Preprocessing

Subject and description are concatenated and lowercased:

```python
text = f"{subject} {description}".lower()
```

### Step 2 — Category Classification (`classifier.py`)

The classifier counts how many keywords from each category appear in the text:

```
text: "I keep getting 500 errors and my billing is wrong"

Billing:   hits = 2  (billing, payment)
Technical: hits = 2  (500, error)
Account:   hits = 0
Feature:   hits = 0
```

The category with the **most hits** wins. Confidence is calculated as:

```
confidence = winner_hits / total_hits_across_all_categories
```

If there are no keyword hits at all, the category defaults to `"Other"` with 0.0 confidence.

**Categories:**

| Category        | Example keywords                                      |
|-----------------|-------------------------------------------------------|
| Billing         | invoice, charge, payment, refund, subscription, fee  |
| Technical       | bug, error, crash, timeout, 500, outage, down         |
| Account         | login, password, locked, 2fa, reset, suspended        |
| Feature Request | feature, suggestion, wishlist, improvement, request   |

### Step 3 — Urgency Detection (`priority.py`)

The combined text is scanned for urgency keywords:

```python
urgency = any(kw in text for kw in URGENCY_KEYWORDS)
```

Urgency keywords include: `urgent`, `asap`, `immediately`, `critical`, `emergency`, `outage`, `production`, `blocker`, `cannot work`, `live issue`, and more.

### Step 4 — Priority Ladder

With `urgency` and `category` known, the system walks the **priority ladder** top-down and returns the first matching rule:

| Rule | Requires Urgency | Restricted to Categories       | Result |
|------|-----------------|--------------------------------|--------|
| 1    | Yes             | Technical, Billing             | **P0** |
| 2    | Yes             | Any                            | **P1** |
| 3    | No              | Billing, Account               | **P2** |
| 4    | No              | Any                            | **P3** |

**Example mappings:**

| Scenario                              | Priority |
|---------------------------------------|----------|
| Urgent + Technical (production down)  | P0       |
| Urgent + Account (locked out ASAP)    | P1       |
| Billing issue (no urgency)            | P2       |
| Feature request                       | P3       |

### Step 5 — Custom Rule Overrides

After the ladder, **custom rules** are evaluated in strict precedence order. A custom rule can **override the priority** (always upward), **override the category**, and **append a flag** to `custom_flags`. See [Custom Rules & Flags](#custom-rules--flags).

### Step 6 — Category Override & Confidence Boost (`analyzer.py`)

The orchestrator applies post-processing:
- If a custom flag mandates a specific category (e.g. `security_escalation` → Technical), the classifier's category is replaced.
- Each flag enforces a minimum confidence value to prevent low-confidence overrides looking wrong in the UI.

### Step 7 — Assemble & Return

An `AnalysisResult` dataclass is returned to the service:

```python
@dataclass
class AnalysisResult:
    category: str        # "Technical" | "Billing" | "Account" | "Feature Request" | "Other"
    priority: str        # "P0" | "P1" | "P2" | "P3"
    urgency: bool        # True if urgency keywords detected
    confidence: float    # 0.0–1.0
    keywords: list[str]  # matched keyword tokens
    custom_flags: list[str]  # e.g. ["security_escalation"]
```

---

## Priority System

| Priority | Label    | Meaning                                              | Typical SLA     |
|----------|----------|------------------------------------------------------|-----------------|
| **P0**   | Critical | System down / security / data loss / legal risk      | Immediate       |
| **P1**   | High     | Urgent issue not covered by P0 criteria              | < 1 hour        |
| **P2**   | Medium   | Billing or account issue, no urgency signal          | < 4 hours       |
| **P3**   | Low      | Feature request or general enquiry                   | Next sprint     |

---

## Custom Rules & Flags

Custom rules are **hard overrides** — they fire after the standard ladder and take precedence over it. They are evaluated in the order shown below (highest precedence first). A ticket can only trigger **one custom P0 rule** (first match wins).

---

### `security_escalation` → **P0 + Technical**

**Triggers on:** `security`, `vulnerability`, `breach`, `exploit`, `data leak`, `hacked`, `hack`, `unauthorized`, `malware`, `ransomware`, `phishing`, `compromised`

**Rationale:** A single security keyword represents potential existential risk to users and the company. Normal keyword-count scoring cannot be trusted here — one signal must unconditionally escalate to the highest priority for immediate human review.

**Example:**
```
Subject:     "Security breach"
Description: "I think my account was hacked"
→ Priority: P0  Category: Technical  Flags: [security_escalation]
```

---

### `compliance_risk` → **P0**

**Triggers on:** `gdpr`, `lawsuit`, `legal action`, `attorney`, `lawyer`, `sue`, `compliance`, `regulation`, `regulatory`, `audit`, `right to erasure`, `data request`, `subpoena`, `court order`

**Rationale:** Legal and regulatory issues carry severe financial and reputational consequences. A GDPR data erasure request or a court order must never sit in a queue — it requires immediate escalation regardless of category.

**Example:**
```
Subject:     "GDPR data erasure request"
Description: "Please delete all my data under right to erasure"
→ Priority: P0  Flags: [compliance_risk]
```

---

### `data_loss` → **P0 + Technical**

**Triggers on:** `data loss`, `lost data`, `deleted`, `corrupted`, `missing data`, `data gone`, `wiped`, `disappeared`, `can't find my`, `restore`, `backup`, `accidentally deleted`

**Rationale:** Lost or corrupted data requires immediate engineering intervention. Data integrity failures are both critical for users and potentially irreversible — they cannot wait in the standard queue.

**Example:**
```
Subject:     "All my files disappeared"
Description: "After the update all my data was wiped"
→ Priority: P0  Category: Technical  Flags: [data_loss]
```

---

### `account_takeover` → **P0 + Account**

**Triggers on:** `account takeover`, `someone else logged in`, `not me`, `suspicious login`, `unrecognised login`, `unrecognized login`, `logged in from`, `strange activity`, `unknown device`, `account stolen`, `hijacked`

**Rationale:** Account takeover signals combine security urgency with account access — the victim may be locked out while an attacker is actively in their account. This requires immediate suspension/investigation.

**Example:**
```
Subject:     "Someone logged into my account"
Description: "I got an alert about a login from an unknown device"
→ Priority: P0  Category: Account  Flags: [account_takeover]
```

---

### `refund_detected` → **P1 + Billing**

**Triggers on:** `refund`, `money back`, `chargeback`

**Rationale:** Refund requests carry direct financial SLA implications. Delayed handling often leads to payment disputes and chargebacks, which incur fees and damage merchant reputation. They need fast billing team attention.

**Example:**
```
Subject:     "Refund request"
Description: "Please process my refund, I cancelled last week"
→ Priority: P1  Category: Billing  Flags: [refund_detected]
```

---

### `pricing_dispute` → **P2 + Billing**

**Triggers on:** `wrong price`, `incorrect price`, `price mismatch`, `overcharged`, `double charged`, `double billed`, `charged twice`, `billed twice`, `unexpected charge`, `unauthorised charge`, `unauthorized charge`

**Rationale:** Pricing discrepancies need billing team review but are not time-critical like refunds or security incidents. P2 ensures they're handled within the same business day.

**Example:**
```
Subject:     "Double charged this month"
Description: "I was billed twice for the same subscription"
→ Priority: P2  Category: Billing  Flags: [pricing_dispute]
```

---

### `spam_likely` → **Informational (no priority change)**

**Triggers on:** `test`, `testing`, `hello`, `hi there`, `ignore`, `asdfgh`, `qwerty`, `123456`, `lorem ipsum`, `sample`, `dummy`

**Rationale:** Test submissions and gibberish tickets waste triage agent time. This flag does not change priority — it serves as a soft signal to routing logic or a human agent to deprioritise review.

**Example:**
```
Subject:     "test"
Description: "testing 123456"
→ Priority: P3  Flags: [spam_likely]
```

---

## API Reference

### `POST /tickets/analyze`

Analyze and persist a new support ticket.

**Request body:**

```json
{
  "subject": "App keeps crashing on login",
  "description": "Getting 500 errors since this morning. Production is down, need urgent fix."
}
```

| Field         | Type   | Required | Constraints             |
|---------------|--------|----------|-------------------------|
| `subject`     | string | Yes      | 1–300 characters        |
| `description` | string | Yes      | 1–5000 characters       |

Both fields are stripped of leading/trailing whitespace automatically.

**Response `201 Created`:**

```json
{
  "id": 42,
  "subject": "App keeps crashing on login",
  "description": "Getting 500 errors since this morning. Production is down, need urgent fix.",
  "category": "Technical",
  "priority": "P0",
  "urgency": true,
  "confidence": 0.83,
  "keywords": ["crash", "500", "error", "production"],
  "custom_flags": [],
  "created_at": "2026-02-26T10:30:00Z"
}
```

**Error responses:**

| Status | Reason                                     |
|--------|--------------------------------------------|
| `422`  | Validation failed (empty fields, too long) |

---

### `GET /tickets`

Return all analyzed tickets, ordered newest first.

**Response `200 OK`:**

```json
{
  "tickets": [
    {
      "id": 42,
      "subject": "App keeps crashing on login",
      "description": "...",
      "category": "Technical",
      "priority": "P0",
      "urgency": true,
      "confidence": 0.83,
      "keywords": ["crash", "500"],
      "custom_flags": [],
      "created_at": "2026-02-26T10:30:00Z"
    }
  ],
  "total": 1
}
```

---

### `GET /health`

Liveness probe for Docker / load balancers.

**Response `200 OK`:**

```json
{ "status": "ok" }
```

---

## Data Model

All tickets are persisted in a single `tickets` table in a SQLite database (`data/tickets.db`).

| Column         | SQL Type    | Notes                                                    |
|----------------|-------------|----------------------------------------------------------|
| `id`           | INTEGER PK  | Auto-increment primary key                               |
| `subject`      | TEXT        | Ticket title (not null)                                  |
| `description`  | TEXT        | Ticket body (not null)                                   |
| `category`     | TEXT        | Classification result: Technical / Billing / Account / Feature Request / Other |
| `priority`     | TEXT        | P0 / P1 / P2 / P3                                        |
| `urgency`      | BOOLEAN     | True if urgency keywords detected                        |
| `confidence`   | FLOAT       | 0.0–1.0; ratio of winning category hits to total hits    |
| `keywords`     | TEXT        | JSON-serialised list of matched keywords                 |
| `custom_flags` | TEXT        | JSON-serialised list of triggered custom rule names      |
| `created_at`   | DATETIME    | UTC timestamp set at insert time                         |

Lists (`keywords`, `custom_flags`) are stored as JSON text and deserialized by helper methods on the ORM model (`get_keywords()`, `get_custom_flags()`).

---

## Frontend Overview

The frontend is a **React 18 + TypeScript + Vite** single-page application styled with plain CSS (no UI framework).

### Components

#### `App.tsx` — Root Shell
- Holds all state: `tickets[]`, `loading`, modal visibility.
- Computes live header stats: total ticket count, P0 (critical) count, P1 (urgent) count.
- Renders a sticky header with a gradient accent bar, brand icon, and real-time stat chips.
- Fetches the ticket list on mount via `GET /tickets`.

#### `TicketForm.tsx` — Submission Form
- Controlled form with `subject` (text input) and `description` (textarea, max 1000 chars).
- Character counter on the description field that turns amber as the limit approaches.
- On submit: calls `POST /tickets/analyze`, shows a loading state ("Analyzing…").
- On success: displays an inline **Analysis Result** panel with category badge, priority badge, urgency indicator, confidence bar, matched keywords, and custom flags — without leaving the page.
- Passes the newly created ticket back to `App.tsx` to update the list instantly.

#### `TicketList.tsx` — Ticket History & Detail Modal
- Displays all past tickets as a **responsive card grid** (auto-fill, min 320px columns).
- Each card shows: ticket ID, relative time (e.g. "5m ago", displayed in **IST — Asia/Kolkata**), subject, category/priority/urgency badges, a mini confidence bar, and any custom flags.
- Clicking a card opens a **detail modal** with full subject, description, all analysis fields, and the exact IST timestamp.
- Loading state shows animated skeleton rows (shimmer effect).
- Empty state shows a document-icon illustration with a helpful prompt.

### API Client (`api/tickets.ts`)

Two typed async functions:

```typescript
analyzeTicket(req: TicketRequest): Promise<Ticket>
listTickets(): Promise<{ tickets: Ticket[]; total: number }>
```

Both functions call the backend and deserialize responses into strongly-typed `Ticket` objects.

### TypeScript Types (`types/ticket.ts`)

```typescript
interface Ticket {
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
```

---

## Configuration Reference

All NLP rules live in `backend/app/config.py`. To modify behaviour, edit only this file.

| Variable                    | Type              | Purpose                                              |
|-----------------------------|-------------------|------------------------------------------------------|
| `CATEGORY_KEYWORDS`         | `Dict[str, List]` | Keywords per category for the classifier             |
| `URGENCY_KEYWORDS`          | `List[str]`       | Words that set `urgency = True`                      |
| `SECURITY_KEYWORDS`         | `List[str]`       | Triggers `security_escalation` → P0                 |
| `REFUND_KEYWORDS`           | `List[str]`       | Triggers `refund_detected` → P1                     |
| `COMPLIANCE_KEYWORDS`       | `List[str]`       | Triggers `compliance_risk` → P0                     |
| `DATA_LOSS_KEYWORDS`        | `List[str]`       | Triggers `data_loss` → P0                           |
| `ACCOUNT_TAKEOVER_KEYWORDS` | `List[str]`       | Triggers `account_takeover` → P0                    |
| `PRICING_DISPUTE_KEYWORDS`  | `List[str]`       | Triggers `pricing_dispute` → P2                     |
| `SPAM_KEYWORDS`             | `List[str]`       | Triggers `spam_likely` (informational only)         |
| `PRIORITY_LADDER`           | `List[tuple]`     | Ordered priority rules `(label, needs_urgency, allowed_categories)` |
| `DB_URL`                    | `str`             | SQLAlchemy async connection string                   |

**To add a new custom rule:**
1. Add a keyword list to `config.py`: `MY_RULE_KEYWORDS = [...]`
2. Import it in `priority.py` and add a check in `_apply_custom_rules()`.
3. Add it to `_FLAG_CATEGORY` / `_FLAG_MIN_CONFIDENCE` in `analyzer.py` if needed.
4. Add unit tests in `tests/test_priority.py`.

No changes to controllers, services, or schemas are needed.

---

## Running Tests

```bash
cd backend
pytest -v
```

**35 tests** across three test files:

| File                    | Coverage                                                   |
|-------------------------|------------------------------------------------------------|
| `test_classifier.py`    | Category classification, confidence scoring, edge cases    |
| `test_priority.py`      | Priority ladder, urgency detection, all 7 custom rules     |
| `test_api.py`           | HTTP integration tests: analyze endpoint, list endpoint    |

All analyzer tests run as **pure unit tests** (no database, no HTTP server) because the analyzers are pure functions.

**Example test run output:**

```
============================================ test session starts =============================================
collected 35 items

tests/test_classifier.py::test_billing_classification PASSED
tests/test_classifier.py::test_technical_classification PASSED
...
tests/test_priority.py::test_security_escalation PASSED
tests/test_priority.py::test_compliance_risk PASSED
tests/test_priority.py::test_data_loss PASSED
tests/test_priority.py::test_account_takeover PASSED
tests/test_priority.py::test_refund_detected PASSED
tests/test_priority.py::test_pricing_dispute PASSED
tests/test_priority.py::test_spam_likely PASSED
...
============================================ 35 passed in 0.42s =============================================
```

---

## Environment & Dependencies

### Backend (`requirements.txt`)

| Package              | Purpose                                           |
|----------------------|---------------------------------------------------|
| `fastapi`            | Web framework                                     |
| `uvicorn[standard]`  | ASGI server                                       |
| `sqlalchemy`         | ORM (async via `asyncio` extension)               |
| `aiosqlite`          | Async SQLite driver                               |
| `pydantic`           | Request/response validation and serialisation     |
| `greenlet`           | Required by SQLAlchemy async on some platforms    |
| `httpx`              | Async HTTP client used in integration tests       |
| `pytest`             | Test runner                                       |
| `pytest-asyncio`     | Async test support                                |

### Frontend

| Package      | Purpose                            |
|--------------|------------------------------------|
| `react` 18   | UI library                         |
| `react-dom`  | DOM renderer                       |
| `typescript` | Static typing                      |
| `vite`       | Build tool and dev server          |

No UI component library is used — all styles are hand-crafted in `index.css` using CSS custom properties (design tokens).

### Docker

| Service  | Base Image                        | Notes                                    |
|----------|-----------------------------------|------------------------------------------|
| backend  | `python:3.11-slim`                | Runs `uvicorn` on port 8000              |
| frontend | `node:18-alpine` + `nginx:alpine` | Multi-stage: build with Node, serve with nginx on port 80 |

`docker-compose.yml` wires the two services together with nginx proxying `/tickets` and `/health` to the backend container.

---

## Design Principles

- **Config over code** — all NLP rules are data in `config.py`; logic never hardcodes strings.
- **Pure functions for analysis** — analyzers have no side effects, making them trivially testable and replaceable.
- **Async everywhere** — non-blocking DB I/O throughout the backend.
- **Strict layering** — controllers don't touch the DB; services don't construct HTTP responses; analyzers don't know about services.
- **No external dependencies for ML** — the pipeline works fully offline and requires no API keys, no model downloads, and no GPU.
- **Production-ready baseline** — Docker, nginx, health checks, CORS, input validation, and integration tests are all included out of the box.

**Demo:**

- Subject: `"Security breach"`, Description: `"I think my account was hacked"` → P0, Technical, `security_escalation`
- Subject: `"Refund request"`, Description: `"Please process my refund"` → P1, Billing, `refund_detected`

---

## Data Model

Single `tickets` table in SQLite:

| Column         | Type        | Notes                                                   |
| -------------- | ----------- | ------------------------------------------------------- |
| `id`           | INTEGER PK  | Auto-increment                                          |
| `subject`      | TEXT        | Ticket title                                            |
| `description`  | TEXT        | Ticket body                                             |
| `category`     | TEXT        | Billing / Technical / Account / Feature Request / Other |
| `priority`     | TEXT        | P0 / P1 / P2 / P3                                       |
| `urgency`      | BOOLEAN     | Urgency keyword detected                                |
| `confidence`   | FLOAT       | 0.0 – 1.0                                               |
| `keywords`     | TEXT (JSON) | Matched keywords                                        |
| `custom_flags` | TEXT (JSON) | e.g. `["security_escalation"]`                          |
| `created_at`   | DATETIME    | UTC                                                     |

---

## Reflection

### Design Decisions

**Single `tickets` table** was chosen over a normalised schema (e.g. separate `keywords` and `flags` tables) because all fields are read-only after creation, there are no relational queries needed, and denormalisation keeps queries trivially simple. JSON columns for arrays avoid premature normalisation at this scale.

**FastAPI + SQLAlchemy async** provides a production-grade foundation with zero-config SQLite for development, while being straightforward to swap to Postgres for production by changing a single `DB_URL` constant.

**Config-driven keyword rules** (`config.py`) mean classification behaviour can be tuned without touching any logic — a non-engineer could adjust keywords in one file.

**Pure-function analyzers** (no DB or framework imports) make the NLP logic trivially unit-testable and reusable outside the web context.

### Trade-offs

- **Keyword matching vs. ML:** Keyword counting is deterministic and explainable but cannot handle synonyms, negation ("not working" matches "working"), or context. A TF-IDF or small transformer model would improve accuracy significantly.
- **Confidence formula:** `winner_hits / total_hits` is a heuristic — it penalises multi-category tickets even when the winner is clearly right. A richer formula (e.g. proportion of possible keywords matched) would be more informative.
- **SQLite:** Suitable for local/demo use. It doesn't support concurrent writes at scale; Postgres would be required in production.
- **No pagination:** `GET /tickets` returns all records. For large datasets, cursor-based pagination would be necessary.

### Limitations

- Keyword list is English-only
- Short or ambiguous tickets will produce low-confidence / "Other" results
- No authentication or multi-tenancy

### What I Would Improve With More Time

1. TF-IDF weighting or a small embedded sentence-transformer for better classification
2. Stemming/lemmatisation (e.g. "crashed" matches "crash") via `nltk` or `spaCy`
3. Postgres + Alembic migrations for production
4. Pagination and filtering on `GET /tickets`
5. Ticket status workflow (open / in-progress / closed)
6. Frontend: edit/resubmit tickets, sortable columns, keyword highlighting
7. Structured logging + observability
