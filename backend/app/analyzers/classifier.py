"""
Category classifier – pure function, no I/O.

Strategy:
  1. Lowercase combined text (subject + description).
  2. Count keyword hits per category (using config.CATEGORY_KEYWORDS).
  3. Winning category = highest hit count.
  4. Confidence = winner_hits / total_hits  (floored at 0.3 when nothing matches).
  5. Return (category, confidence, matched_keywords).
"""
from typing import Tuple

from app.config import CATEGORY_KEYWORDS

MIN_CONFIDENCE = 0.3
OTHER_CATEGORY = "Other"


def classify(subject: str, description: str) -> Tuple[str, float, list[str]]:
    """
    Classify a ticket into a category.

    Returns:
        (category, confidence, matched_keywords)
    """
    text = f"{subject} {description}".lower()

    hits: dict[str, list[str]] = {cat: [] for cat in CATEGORY_KEYWORDS}

    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                hits[category].append(kw)

    # Tally
    counts = {cat: len(kws) for cat, kws in hits.items()}
    total_hits = sum(counts.values())

    if total_hits == 0:
        return OTHER_CATEGORY, MIN_CONFIDENCE, []

    winner = max(counts, key=lambda c: counts[c])
    winner_hits = counts[winner]
    confidence = round(winner_hits / total_hits, 4)
    # Collect all matched keywords across all categories
    matched = [kw for kws in hits.values() for kw in kws]

    return winner, confidence, matched
