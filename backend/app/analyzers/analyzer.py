"""
Analyzer orchestrator.

Combines classifier + priority detector into a single AnalysisResult.
No I/O – all inputs/outputs are plain Python values.
"""
from dataclasses import dataclass, field

from app.analyzers.classifier import classify
from app.analyzers.priority import detect_priority


@dataclass
class AnalysisResult:
    category: str
    priority: str
    urgency: bool
    confidence: float
    keywords: list[str]
    custom_flags: list[str]


def analyze(subject: str, description: str) -> AnalysisResult:
    """
    Full analysis pipeline:
      1. classify text → category, confidence, matched keywords
      2. detect priority, urgency, custom flags
      3. apply custom-rule category overrides (security/refund may change category)
      4. return AnalysisResult
    """
    category, confidence, keywords = classify(subject, description)
    priority, urgency, custom_flags = detect_priority(subject, description, category)

    # Custom rules may override the classifier's category
    _FLAG_CATEGORY: dict[str, str] = {
        "security_escalation": "Technical",
        "data_loss": "Technical",
        "account_takeover": "Account",
        "refund_detected": "Billing",
        "pricing_dispute": "Billing",
    }
    _FLAG_MIN_CONFIDENCE: dict[str, float] = {
        "security_escalation": 0.95,
        "compliance_risk": 0.90,
        "data_loss": 0.90,
        "account_takeover": 0.90,
        "refund_detected": 0.80,
        "pricing_dispute": 0.75,
    }

    for flag in custom_flags:
        if flag in _FLAG_CATEGORY:
            category = _FLAG_CATEGORY[flag]
        if flag in _FLAG_MIN_CONFIDENCE:
            confidence = max(confidence, _FLAG_MIN_CONFIDENCE[flag])

    return AnalysisResult(
        category=category,
        priority=priority,
        urgency=urgency,
        confidence=round(confidence, 4),
        keywords=list(dict.fromkeys(keywords)),  # deduplicate, preserve order
        custom_flags=custom_flags,
    )
