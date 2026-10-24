"""
PANAS (Positive and Negative Affect Schedule) scoring module.

The instrument contains 20 items:
    * Items 1‑10  → Positive Affect (PA)
    * Items 11‑20 → Negative Affect (NA)

Each item is scored 1‑5. Subscale scores are the sum of the respective 10 items.
"""

from typing import List, Tuple, Dict

def _validate_responses(responses: List[int]) -> None:
    if len(responses) != 20:
        raise ValueError(f"PANAS requires exactly 20 responses, got {len(responses)}")
    for i, r in enumerate(responses):
        if not isinstance(r, int):
            raise ValueError(f"Response {i} is not an integer: {r!r}")
        if not (1 <= r <= 5):
            raise ValueError(f"Response {i} out of valid range 1‑5: {r}")

def score_panas(responses: List[int]) -> Dict[str, int | str]:
    """
    Compute PANAS subscale scores and a quality flag.

    Args:
        responses: List of 20 integer responses (1‑5).

    Returns:
        Dictionary with:
            - 'positive_score' (int): Sum of the first 10 items.
            - 'negative_score' (int): Sum of the last 10 items.
            - 'quality_flag' (str): Always 'valid' for PANAS.

    Raises:
        ValueError: If the input list is malformed or contains out‑of‑range values.
    """
    _validate_responses(responses)

    pa_items = responses[:10]
    na_items = responses[10:]

    pa_score = sum(pa_items)
    na_score = sum(na_items)

    return {
        'positive_score': int(pa_score),
        'negative_score': int(na_score),
        'quality_flag': 'valid'
    }