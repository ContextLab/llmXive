"""
panas.py

Scoring implementation for the Positive and Negative Affect Schedule (PANAS).
The function expects 20 integer responses (1‑5) ordered with the first
ten items representing Positive Affect (PA) and the last ten representing
Negative Affect (NA).  It returns a tuple ``(pa_score, na_score)``.
"""

from typing import List, Tuple

class PANASError(ValueError):
    """Custom error for PANAS validation failures."""

def score_panas(responses: List[int]) -> Tuple[int, int]:
    """
    Compute PANAS scores.

    Parameters
    ----------
    responses : List[int]
        A list of 20 integer responses (1‑5).  Items 0‑9 correspond to
        Positive Affect, items 10‑19 to Negative Affect.

    Returns
    -------
    Tuple[int, int]
        (positive_affect_score, negative_affect_score)

    Raises
    ------
    PANASError
        If the length is not 20 or any response is outside the allowed range.
    """
    if len(responses) != 20:
        raise PANASError(
            f"PANAS requires exactly 20 responses, got {len(responses)}."
        )
    for i, r in enumerate(responses):
        if not isinstance(r, int):
            raise PANASError(f"Response {i} is not an integer: {r!r}")
        if r < 1 or r > 5:
            raise PANASError(
                f"Response {i} out of range (1‑5): {r}"
            )
    # First 10 items = Positive Affect, last 10 = Negative Affect
    pa = sum(responses[:10])
    na = sum(responses[10:])
    return int(pa), int(na)
