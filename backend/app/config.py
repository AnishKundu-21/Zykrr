"""
Config-driven keyword rules for the ticket analyzer.
All classification logic is data — not hardcoded in functions.
"""
from typing import Dict, List

# ---------------------------------------------------------------------------
# Category classification keywords
# ---------------------------------------------------------------------------
CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "Billing": [
        "invoice", "charge", "payment", "refund", "subscription",
        "billing", "price", "overcharged", "bill", "cost", "fee",
        "transaction", "receipt", "paid", "debit", "credit card",
    ],
    "Technical": [
        "bug", "error", "crash", "slow", "not working", "broken",
        "timeout", "500", "outage", "down", "fail", "failure",
        "exception", "issue", "glitch", "performance", "latency",
        "503", "404", "unavailable",
    ],
    "Account": [
        "login", "password", "account", "locked", "access", "reset",
        "2fa", "mfa", "sign in", "sign-in", "username", "email",
        "profile", "permissions", "suspended", "banned", "blocked",
    ],
    "Feature Request": [
        "feature", "suggestion", "would be nice", "wishlist",
        "improvement", "add support", "request", "enhance",
        "could you", "please add", "missing", "need ability",
    ],
}

# ---------------------------------------------------------------------------
# Urgency detection keywords
# ---------------------------------------------------------------------------
URGENCY_KEYWORDS: List[str] = [
    "urgent", "asap", "immediately", "critical", "emergency",
    "down", "outage", "blocker", "now", "right away", "as soon as",
    "cannot work", "can't work", "production", "live issue",
]

# ---------------------------------------------------------------------------
# Custom rule: Security escalation  →  always P0 + Technical
# Rationale: a single security signal represents existential risk;
#            must override all other signals unconditionally.
# ---------------------------------------------------------------------------
SECURITY_KEYWORDS: List[str] = [
    "security", "vulnerability", "breach", "exploit",
    "data leak", "hacked", "hack", "unauthorized", "malware",
    "ransomware", "phishing", "compromised",
]

# ---------------------------------------------------------------------------
# Custom rule: Refund escalation  →  at least P1 + Billing
# Rationale: refunds carry direct financial SLA implications.
# ---------------------------------------------------------------------------
REFUND_KEYWORDS: List[str] = [
    "refund", "money back", "chargeback",
]

# ---------------------------------------------------------------------------
# Custom rule: Compliance / legal risk  →  P0 + flag compliance_risk
# Rationale: any mention of legal action, GDPR, lawsuits must be escalated
#            immediately to avoid regulatory consequences.
# ---------------------------------------------------------------------------
COMPLIANCE_KEYWORDS: List[str] = [
    "gdpr", "lawsuit", "legal action", "attorney", "lawyer",
    "sue", "compliance", "regulation", "regulatory", "audit",
    "right to erasure", "data request", "subpoena", "court order",
]

# ---------------------------------------------------------------------------
# Custom rule: Data loss  →  P0 + Technical + flag data_loss
# Rationale: lost or corrupted data requires immediate engineering response.
# ---------------------------------------------------------------------------
DATA_LOSS_KEYWORDS: List[str] = [
    "data loss", "lost data", "deleted", "corrupted", "missing data",
    "data gone", "wiped", "disappeared", "can't find my", "restore",
    "backup", "accidentally deleted",
]

# ---------------------------------------------------------------------------
# Custom rule: Account takeover  →  P0 + Account + flag account_takeover
# Rationale: active takeover attempts combine security + account urgency.
# ---------------------------------------------------------------------------
ACCOUNT_TAKEOVER_KEYWORDS: List[str] = [
    "account takeover", "someone else logged in", "not me",
    "suspicious login", "unrecognised login", "unrecognized login",
    "logged in from", "strange activity", "unknown device",
    "account stolen", "hijacked",
]

# ---------------------------------------------------------------------------
# Custom rule: Pricing dispute  →  at least P2 + Billing + flag pricing_dispute
# Rationale: disputed prices need billing team review but aren't critical.
# ---------------------------------------------------------------------------
PRICING_DISPUTE_KEYWORDS: List[str] = [
    "wrong price", "incorrect price", "price mismatch", "overcharged",
    "double charged", "double billed", "charged twice", "billed twice",
    "unexpected charge", "unauthorised charge", "unauthorized charge",
]

# ---------------------------------------------------------------------------
# Custom rule: Spam / noise detection  →  flag spam_likely, do NOT escalate
# Rationale: test tickets, gibberish, or one-word submissions waste triage time.
# ---------------------------------------------------------------------------
SPAM_KEYWORDS: List[str] = [
    "test", "testing", "hello", "hi there", "ignore", "asdfgh",
    "qwerty", "123456", "lorem ipsum", "sample", "dummy",
]

# ---------------------------------------------------------------------------
# Priority rule ladder  (evaluated top-down; first match wins)
# Each entry: (priority_label, requires_urgency, restrict_to_categories)
# restrict_to_categories=None means "any category"
# ---------------------------------------------------------------------------
PRIORITY_LADDER = [
    ("P0", True,  ["Technical", "Billing"]),
    ("P1", True,  None),
    ("P2", False, ["Billing", "Account"]),
    ("P3", False, None),   # default fallback
]

# ---------------------------------------------------------------------------
# Misc
# ---------------------------------------------------------------------------
DB_URL = "sqlite+aiosqlite:///./data/tickets.db"
