"""
Priority & urgency detector – pure function, no I/O.

Strategy:
  1. Scan combined text for URGENCY_KEYWORDS → urgency bool.
  2. Walk PRIORITY_LADDER top-down; first matching rule wins.
  3. Apply custom rules (security / refund) which can *override* ladder result.
  4. Return (priority, urgency, custom_flags).
"""
from typing import Optional, Tuple

from app.config import (
    ACCOUNT_TAKEOVER_KEYWORDS,
    COMPLIANCE_KEYWORDS,
    DATA_LOSS_KEYWORDS,
    PRICING_DISPUTE_KEYWORDS,
    PRIORITY_LADDER,
    REFUND_KEYWORDS,
    SECURITY_KEYWORDS,
    SPAM_KEYWORDS,
    URGENCY_KEYWORDS,
)


def detect_priority(
    subject: str,
    description: str,
    category: str,
) -> Tuple[str, bool, list[str]]:
    """
    Determine ticket priority and detect urgency / custom signals.

    Returns:
        (priority, urgency, custom_flags)
    """
    text = f"{subject} {description}".lower()

    # --- Urgency detection ---
    urgency = any(kw in text for kw in URGENCY_KEYWORDS)

    # --- Priority ladder ---
    priority = _apply_ladder(urgency, category)

    # --- Custom rules (may override) ---
    custom_flags: list[str] = []
    priority, category_override = _apply_custom_rules(text, priority, custom_flags)

    return priority, urgency, custom_flags


def _apply_ladder(urgency: bool, category: str) -> str:
    for label, needs_urgency, allowed_categories in PRIORITY_LADDER:
        urgency_ok = (not needs_urgency) or urgency
        category_ok = (allowed_categories is None) or (category in allowed_categories)
        if urgency_ok and category_ok:
            return label
    return "P3"  # should never reach here due to last rule, but safety net


def _apply_custom_rules(
    text: str, priority: str, custom_flags: list[str]
) -> Tuple[str, Optional[str]]:
    """
    Apply hard-override custom rules (evaluated in precedence order).

    P0 overrides (highest precedence, return immediately):
      - security_escalation  : any security keyword
      - compliance_risk      : legal/GDPR/regulatory keywords
      - data_loss            : data deletion / corruption keywords
      - account_takeover     : active hijack signals

    P1 overrides:
      - refund_detected      : refund / chargeback keywords

    P2 overrides:
      - pricing_dispute      : overcharged / double-billed keywords

    Informational flags (no priority change):
      - spam_likely          : test/gibberish submissions
    """
    _ORDER = ["P0", "P1", "P2", "P3"]

    def escalate_to(target: str) -> str:
        """Raise priority to target if current is lower."""
        if _ORDER.index(priority) > _ORDER.index(target):
            return target
        return priority

    category_override: Optional[str] = None

    # --- P0 rules (return immediately on first match) ---

    if any(kw in text for kw in SECURITY_KEYWORDS):
        custom_flags.append("security_escalation")
        return "P0", "Technical"

    if any(kw in text for kw in COMPLIANCE_KEYWORDS):
        custom_flags.append("compliance_risk")
        return "P0", None   # keep classifier category; legal can be any domain

    if any(kw in text for kw in DATA_LOSS_KEYWORDS):
        custom_flags.append("data_loss")
        return "P0", "Technical"

    if any(kw in text for kw in ACCOUNT_TAKEOVER_KEYWORDS):
        custom_flags.append("account_takeover")
        return "P0", "Account"

    # --- P1 rules ---

    if any(kw in text for kw in REFUND_KEYWORDS):
        custom_flags.append("refund_detected")
        category_override = "Billing"
        return escalate_to("P1"), category_override

    # --- P2 rules ---

    if any(kw in text for kw in PRICING_DISPUTE_KEYWORDS):
        custom_flags.append("pricing_dispute")
        category_override = "Billing"
        return escalate_to("P2"), category_override

    # --- Informational flags (no escalation) ---

    if any(kw in text for kw in SPAM_KEYWORDS):
        custom_flags.append("spam_likely")
        # intentionally no priority change

    return priority, category_override
