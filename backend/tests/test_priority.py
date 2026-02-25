"""Unit tests for the priority detector."""
import pytest
from app.analyzers.priority import detect_priority


# ---------------------------------------------------------------------------
# Urgency detection
# ---------------------------------------------------------------------------


def test_urgency_detected_asap():
    _, urgency, _ = detect_priority("Help", "Need this fixed asap", "Technical")
    assert urgency is True


def test_urgency_detected_outage():
    _, urgency, _ = detect_priority("Outage", "Production is down right now", "Technical")
    assert urgency is True


def test_no_urgency():
    _, urgency, _ = detect_priority("Question", "How do I reset my password?", "Account")
    assert urgency is False


# ---------------------------------------------------------------------------
# Priority ladder
# ---------------------------------------------------------------------------


def test_p0_urgent_technical():
    priority, _, _ = detect_priority("URGENT", "system is down asap", "Technical")
    assert priority == "P0"


def test_p0_urgent_billing():
    priority, _, _ = detect_priority("URGENT", "payment failure critical", "Billing")
    assert priority == "P0"


def test_p1_urgent_other_category():
    priority, _, _ = detect_priority("URGENT", "urgent feature request", "Feature Request")
    assert priority == "P1"


def test_p2_billing_no_urgency():
    priority, _, _ = detect_priority("Invoice", "I have a billing question", "Billing")
    assert priority == "P2"


def test_p2_account_no_urgency():
    priority, _, _ = detect_priority("Account", "Please reset my account", "Account")
    assert priority == "P2"


def test_p3_feature_request():
    priority, _, _ = detect_priority("Idea", "Add dark mode please", "Feature Request")
    assert priority == "P3"


def test_p3_other():
    priority, _, _ = detect_priority("Hi", "Just saying hello", "Other")
    assert priority == "P3"


# ---------------------------------------------------------------------------
# Custom rules
# ---------------------------------------------------------------------------


def test_security_escalation_to_p0():
    """Security keyword must force P0 regardless of other signals."""
    priority, _, flags = detect_priority("Problem", "possible security breach detected", "Other")
    assert priority == "P0"
    assert "security_escalation" in flags


def test_security_escalation_overrides_p3():
    priority, _, flags = detect_priority("Suggestion", "vulnerability in the export feature", "Feature Request")
    assert priority == "P0"
    assert "security_escalation" in flags


def test_refund_escalation_at_least_p1():
    """Refund keyword on a low-priority ticket must escalate to P1."""
    priority, _, flags = detect_priority("Refund", "I want a refund please", "Other")
    assert priority == "P1"
    assert "refund_detected" in flags


def test_refund_does_not_downgrade_p0():
    """Refund on an already P0 ticket stays P0."""
    priority, _, flags = detect_priority("Critical refund", "urgent refund asap outage", "Billing")
    assert priority == "P0"
    assert "refund_detected" in flags


def test_security_takes_precedence_over_refund():
    """Both security + refund keywords → security rule wins (P0)."""
    priority, _, flags = detect_priority(
        "Security refund",
        "security breach and I want a refund",
        "Billing",
    )
    assert priority == "P0"
    assert "security_escalation" in flags


# ---------------------------------------------------------------------------
# New custom flags
# ---------------------------------------------------------------------------


def test_compliance_risk_p0():
    priority, _, flags = detect_priority(
        "GDPR request", "I want to exercise my right to erasure under GDPR", "Account"
    )
    assert priority == "P0"
    assert "compliance_risk" in flags


def test_legal_action_compliance_risk():
    priority, _, flags = detect_priority(
        "Legal action", "I am consulting my attorney about this issue", "Other"
    )
    assert priority == "P0"
    assert "compliance_risk" in flags


def test_data_loss_p0():
    priority, _, flags = detect_priority(
        "Lost everything", "All my data is gone, I accidentally deleted my project", "Technical"
    )
    assert priority == "P0"
    assert "data_loss" in flags


def test_data_loss_corrupted():
    priority, _, flags = detect_priority(
        "Corrupted file", "My file is corrupted and missing data", "Technical"
    )
    assert priority == "P0"
    assert "data_loss" in flags


def test_account_takeover_p0():
    priority, _, flags = detect_priority(
        "Suspicious login", "There was a suspicious login from an unknown device", "Account"
    )
    assert priority == "P0"
    assert "account_takeover" in flags


def test_account_takeover_not_me():
    priority, _, flags = detect_priority(
        "Not me", "Someone else logged in to my account and it was not me", "Account"
    )
    assert priority == "P0"
    assert "account_takeover" in flags


def test_pricing_dispute_at_least_p2():
    priority, _, flags = detect_priority(
        "Double charged", "I was charged twice for the same subscription", "Billing"
    )
    assert priority in ("P0", "P1", "P2")
    assert "pricing_dispute" in flags


def test_pricing_dispute_does_not_downgrade():
    """pricing_dispute on an already P1 ticket (urgent) should stay P1."""
    priority, _, flags = detect_priority(
        "Urgent billing", "urgent double charged on my account", "Billing"
    )
    # urgency + billing → P0 from ladder, pricing_dispute escalate_to(P2) keeps P0
    assert priority == "P0"
    assert "pricing_dispute" in flags


def test_spam_likely_flag_no_escalation():
    priority, _, flags = detect_priority("Testing", "this is just a test", "Other")
    assert "spam_likely" in flags
    assert priority == "P3"   # flag must NOT change a low-priority ticket


def test_spam_likely_does_not_affect_higher_priority():
    """A real urgent ticket that happens to contain 'test' stays urgent."""
    priority, urgency, flags = detect_priority(
        "Test environment down", "our test production environment is down asap", "Technical"
    )
    assert urgency is True
    assert priority == "P0"
    assert "spam_likely" in flags   # flag still set, but priority unchanged


def test_p0_rules_take_precedence_over_spam():
    """Security + spam keywords → security wins (P0), spam_likely NOT set."""
    priority, _, flags = detect_priority(
        "Security test", "testing for vulnerability in login", "Technical"
    )
    assert priority == "P0"
    assert "security_escalation" in flags
    assert "spam_likely" not in flags   # security short-circuits before spam check

