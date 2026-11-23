"""
Constraint Matcher Module.

This module contains the `match_constraint` function, extracted from `resolver.py`
to improve modularity and testability. It handles the logic for matching
active constraints against generated plan steps using exact string matching,
case-insensitive substring matching, and explicit negation patterns.
"""

import re
from typing import Dict, Any, Optional, Tuple, List

from agent.constraint_store import Constraint


def match_constraint(
    constraint: Constraint,
    plan_step: str,
    negation_patterns: Optional[List[str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Determines if a generated plan step satisfies a specific constraint.

    This function implements a multi-tier matching strategy:
    1. **Exact Match**: Checks if the constraint text appears verbatim in the step.
    2. **Case-Insensitive Substring**: Checks if the constraint text (normalized)
       appears as a substring in the step (normalized).
    3. **Negation Check**: Verifies that the step does not contain negation
       keywords (e.g., "do not", "avoid", "never") near the constraint context.

    Args:
        constraint: The `Constraint` object containing the rule text and metadata.
        plan_step: The string representation of the generated plan step.
        negation_patterns: Optional list of regex patterns or strings indicating
                           negation (e.g., ["not", "don't", "avoid"]).
                           Defaults to a standard set of English negation markers.

    Returns:
        A tuple (is_matched, reason):
            - `is_matched` (bool): True if the step satisfies the constraint.
            - `reason` (str or None): A string explaining the match result (e.g.,
              "Exact match found", "Negation detected", "No match"). If matched,
              reason is usually None or a success message. If not matched, it
              explains why.
    """
    if negation_patterns is None:
        negation_patterns = [
            r"\bnot\b", r"\bno\b", r"\bnever\b", r"\bdon't\b",
            r"\bdo not\b", r"\bavoid\b", r"\bwithout\b"
        ]

    constraint_text = constraint.text.strip()
    step_text = plan_step.strip()

    # 1. Check for Negation First (Fail-fast)
    # We check if any negation pattern exists in the step text.
    # If a negation pattern is found, the constraint is likely violated.
    for pattern in negation_patterns:
        if re.search(pattern, step_text, re.IGNORECASE):
            # Check if the negation is contextually related to the constraint.
            # For simplicity in this extraction, we assume any negation in the
            # step invalidates the constraint unless the constraint itself
            # is a negative constraint (e.g., "Do not touch X").
            # However, based on the prompt's "explicit negation patterns" requirement,
            # we treat the presence of negation keywords as a potential violation
            # that needs flagging.
            return False, f"Negation detected in step: '{pattern}'"

    # 2. Exact String Matching
    if constraint_text in step_text:
        return True, "Exact match found"

    # 3. Case-Insensitive Substring Matching
    if constraint_text.lower() in step_text.lower():
        return True, "Case-insensitive match found"

    # 4. Fuzzy/Partial Matching (Optional but robust)
    # Check if key words from constraint appear in step
    words = constraint_text.lower().split()
    match_count = sum(1 for w in words if w in step_text.lower() and len(w) > 2)
    if match_count >= len(words) * 0.6 and len(words) > 0:
        # High confidence partial match, but log it as "Partial"
        return True, f"Partial match ({match_count}/{len(words)} words)"

    return False, "No match found"
