"""Unit tests for the category classifier."""
import pytest
from app.analyzers.classifier import classify


# ---------------------------------------------------------------------------
# Category detection
# ---------------------------------------------------------------------------


def test_billing_category():
    cat, conf, kws = classify("Payment failed", "I was overcharged on my invoice")
    assert cat == "Billing"
    assert conf > 0.5
    assert any(k in kws for k in ["payment", "overcharged", "invoice"])


def test_technical_category():
    cat, conf, kws = classify("App crash", "Getting a 500 error and timeout on every request")
    assert cat == "Technical"
    assert conf > 0.5


def test_account_category():
    cat, conf, kws = classify("Login problem", "My account is locked and I cannot reset my password")
    assert cat == "Account"
    assert conf > 0.5


def test_feature_request_category():
    cat, conf, kws = classify("Feature request", "It would be nice to add support for dark mode")
    assert cat == "Feature Request"
    assert conf > 0.5


def test_other_category_no_match():
    cat, conf, kws = classify("Hello", "This is a random message with no keywords")
    assert cat == "Other"
    assert conf == 0.3
    assert kws == []


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------


def test_high_confidence_single_category():
    """All keywords from one category → confidence should be 1.0."""
    cat, conf, kws = classify("Bug report", "bug error crash timeout broken")
    assert cat == "Technical"
    assert conf == 1.0


def test_overlap_confidence_less_than_one():
    """Keywords spanning two categories → confidence < 1."""
    cat, conf, kws = classify("Billing bug", "payment error invoice crash")
    assert conf < 1.0


# ---------------------------------------------------------------------------
# Keyword extraction
# ---------------------------------------------------------------------------


def test_matched_keywords_returned():
    _, _, kws = classify("Invoice issue", "I have a billing and payment question")
    for expected in ["invoice", "billing", "payment"]:
        assert expected in kws


def test_no_duplicate_keywords():
    """Same keyword appearing twice in text should not duplicate in results."""
    _, _, kws = classify("bug bug", "bug")
    assert kws.count("bug") == 1
