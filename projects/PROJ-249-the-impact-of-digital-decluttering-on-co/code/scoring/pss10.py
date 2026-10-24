"""
Perceived Stress Scale (PSS‑10) scoring module.

The PSS‑10 consists of 10 items, each scored 0‑4.
The total score is the sum of all items, ranging from 0 to 40.
"""

from typing import List

def score_pss10(responses: List[int]) -> Dict[str, int | str]:
    """
    Compute the PSS‑10 total score and a quality flag.

    Args:
        responses: List of 10 integer responses, each in the range 0‑4.

    Returns:
        Dictionary with:
            - 'total_score' (int): Sum of the responses (0‑40).
            - 'quality_flag' (str): Always 'valid' for PSS‑10 (no RT limits).

    Raises:
        ValueError: If the number of responses is not 10 or any response is out of range.
    """
    if len(responses) != 10:
        raise ValueError(f"PSS‑10 requires exactly 10 responses, got {len(responses)}")

    for i, r in enumerate(responses):
        if not isinstance(r, int):
            raise ValueError(f"Response {i} is not an integer: {r!r}")
        if not (0 <= r <= 4):
            raise ValueError(f"Response {i} out of valid range 0‑4: {r}")

    total = int(sum(responses))
    return {
        'total_score': total,
        'quality_flag': 'valid'
    }
