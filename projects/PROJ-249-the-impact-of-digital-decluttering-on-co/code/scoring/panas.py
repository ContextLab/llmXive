"""
PANAS (Positive and Negative Affect Schedule) scoring module.

The instrument contains 20 items:
    * Items 1‑10  → Positive Affect (PA)
    * Items 11‑20 → Negative Affect (NA)

Each item is scored 1‑5. Subscale scores are the sum of the respective 10 items.
"""

from typing import List, Tuple

def _validate_responses(responses: List[int]) -> None:
    if len(responses) != 20:
        raise ValueError(f"PANAS requires exactly 20 responses, got {len(responses)}")
    for i, r in enumerate(responses):
        if not isinstance(r, int):
            raise ValueError(f"Response {i} is not an integer: {r!r}")
        if not (1 <= r <= 5):
            raise ValueError(f"Response {i} out of valid range 1‑5: {r}")

def score_panas(responses: List[int]) -> Tuple[int, int]:
    """
    Compute PANAS subscale scores.

    Args:
        responses: List of 20 integer responses (1‑5).

    Returns:
        Tuple (pa_score, na_score) where each is the sum of its 10 items.

    Raises:
        ValueError: If the input list is malformed or contains out‑of‑range values.
    """
    _validate_responses(responses)

    pa_items = responses[:10]
    na_items = responses[10:]

    pa_score = sum(pa_items)
    na_score = sum(na_items)

    return int(pa_score), int(na_score)
