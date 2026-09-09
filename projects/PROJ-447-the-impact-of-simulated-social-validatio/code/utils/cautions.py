"""
Causal language scanner for the llmXive automated science pipeline.

This module provides a list of causal trigger words and a scanner function
to reject reports that contain them, ensuring "associational" framing is
maintained in accordance with FR-006.
"""

from typing import List, Optional, Tuple

# List of causal trigger words that should not appear in reports.
# These words imply causality where only association has been demonstrated.
CAUSAL_TRIGGER_WORDS: List[str] = [
    "causes",
    "caused",
    "causing",
    "leads to",
    "led to",
    "leading to",
    "results in",
    "resulted in",
    "resulting in",
    "determines",
    "determined",
    "determining",
    "influences",
    "influenced",
    "influencing",
    "affects",
    "affected",
    "affecting",
    "drives",
    "drove",
    "driving",
    "triggers",
    "triggered",
    "triggering",
    "induces",
    "induced",
    "inducing",
    "promotes",
    "promoted",
    "promoting",
    "predicts",
    "predicted",
    "predicting",  # Often misused for causality
    "is responsible for",
    "responsible for",
    "is the cause of",
    "cause of",
    "effect of",
    "impact of",  # Ambiguous, often implies causality
    "impacts",
    "impacted",
    "impacting",
    "contributes to",  # Can be ambiguous, often implies causality
    "contributes in",
    "due to",
    "because of",
    "stem from",
    "stems from",
    "stems from",
    "arises from",
    "arose from",
    "originates from",
    "originated from",
    "is associated with",  # Often used correctly, but flagged for review if context implies causality
    "linked to",  # Can be ambiguous
    "linked with",
    "correlates with",  # Often used correctly, but flagged if context implies causality
    "correlates to",
    "is a sign of",
    "sign of",
    "indicates",  # Can be ambiguous
    "suggests",  # Can be ambiguous
    "implies",  # Can be ambiguous
]

def scan_report_for_causal_language(report_text: str) -> Tuple[bool, List[str]]:
    """
    Scans a report text for causal trigger words.

    Args:
        report_text (str): The text of the report to scan.

    Returns:
        Tuple[bool, List[str]]: A tuple where the first element is a boolean
            indicating if any causal trigger words were found (True if found),
            and the second element is a list of the unique trigger words found.
    """
    if not report_text:
        return False, []

    found_words = set()
    report_lower = report_text.lower()

    # Check for each trigger word in the report text.
    # Using a simple substring search for now, which is case-insensitive.
    # For more sophisticated NLP, a library like spaCy could be used,
    # but for this task, a direct string match is sufficient.
    for word in CAUSAL_TRIGGER_WORDS:
        if word in report_lower:
            found_words.add(word)

    is_violation = len(found_words) > 0
    return is_violation, sorted(list(found_words))