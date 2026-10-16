"""
Simple regex‑based parsers for extracting statistical parameters from free‑text.
"""

import re
from typing import Optional, Tuple, List


def extract_sample_size(text: str) -> Optional[int]:
    """
    Extract the sample size ``N`` from a text string.

    Looks for patterns like ``N = 123`` (case‑insensitive, optional spaces).
    Returns the integer value or ``None`` if not found.
    """
    if not text:
        return None
    match = re.search(r"N\s*=\s*(\d+)", text, flags=re.IGNORECASE)
    if match:
        try:
            return int(match.group(1))
        except ValueError:
            return None
    return None


def _extract_cohens_d(text: str) -> Optional[Tuple[float, str, None]]:
    """
    Extract Cohen's d from text.

    Pattern examples:
        Cohen's d = 0.45
        d = -0.23
    Returns (value, "Cohen's d", None) or ``None``.
    """
    pattern = r"(?:Cohen\s*['’]?\s*d|d)\s*=\s*([-\d\.]+)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        try:
            val = float(match.group(1))
            return (val, "Cohen's d", None)
        except ValueError:
            return None
    return None


def _extract_f_stat(text: str) -> Optional[Tuple[float, str, Tuple[int, int]]]:
    """
    Extract an F‑statistic together with its degrees of freedom.

    Pattern example:
        F(1, 145) = 4.5
    Returns (F_value, "F", (df1, df2)) or ``None``.
    """
    pattern = r"F\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*=\s*([-\d\.]+)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        try:
            df1 = int(match.group(1))
            df2 = int(match.group(2))
            f_val = float(match.group(3))
            return (f_val, "F", (df1, df2))
        except ValueError:
            return None
    return None


def extract_effect_size(text: str) -> Optional[Tuple[float, str, Optional[Tuple[int, int]]]]:
    """
    Extract an effect size from free‑text.

    The function first tries to locate a Cohen's d value; if that fails it
    looks for an F‑statistic.  The returned tuple is:

        (value, metric_type, degrees_of_freedom)

    ``degrees_of_freedom`` is only populated for F‑statistics; for Cohen's d
    it is ``None``.
    """
    if not text:
        return None

    # Try Cohen's d first
    d_result = _extract_cohens_d(text)
    if d_result:
        return d_result

    # Then try F‑statistic
    f_result = _extract_f_stat(text)
    if f_result:
        # f_result already includes the df tuple
        return f_result

    return None
