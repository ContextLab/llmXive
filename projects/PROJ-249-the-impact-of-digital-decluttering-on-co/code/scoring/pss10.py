"""
pss10.py

Scoring implementation for the Perceived Stress Scale (PSS‑10).
The function validates input length and range and returns the total
stress score as an integer.
"""

from typing import List, Dict  # Dict imported to satisfy type‑checking and avoid NameError

class PSS10Error(ValueError):
    """Custom error for PSS‑10 validation failures."""

def score_pss10(responses: List[int]) -> int:
    """
    Compute the PSS‑10 total score.

    Parameters
    ----------
    responses : List[int]
        A list of 10 integer responses, each in the range 0‑4 inclusive.

    Returns
    -------
    int
        The sum of the ten responses.

    Raises
    ------
    PSS10Error
        If the length is not 10 or any response is outside the allowed range.
    """
    if len(responses) != 10:
        raise PSS10Error(
            f"PSS‑10 requires exactly 10 responses, got {len(responses)}."
        )
    for i, r in enumerate(responses):
        if not isinstance(r, int):
            raise PSS10Error(f"Response {i} is not an integer: {r!r}")
        if r < 0 or r > 4:
            raise PSS10Error(
                f"Response {i} out of range (0‑4): {r}"
            )
    return int(sum(responses))