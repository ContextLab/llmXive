"""
utils/parsers.py
----------------
Regex‑based helpers for extracting statistical parameters from free‑text.

The public helpers raise :class:`DataFetchError` when the required pattern
cannot be found – callers are expected to catch this and record an
``unparseable`` status.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

from .api_client import DataFetchError

__all__ = [
    "extract_sample_size",
    "extract_effect_size",
]

# ----------------------------------------------------------------------
# Sample size extraction
# ----------------------------------------------------------------------
_SAMPLE_SIZE_RE = re.compile(r"N\s*=\s*(\d+)", re.IGNORECASE)

def extract_sample_size(text: str) -> int:
    """
    Extract the sample size ``N`` from ``text``.

    The function looks for the pattern ``N = <integer>`` (case‑insensitive)
    and returns the integer value.

    Parameters
    ----------
    text:
        The raw text (full‑text or abstract) to scan.

    Returns
    -------
    int
        The extracted sample size.

    Raises
    ------
    DataFetchError
        If the pattern cannot be located.
    """
    match = _SAMPLE_SIZE_RE.search(text)
    if not match:
        raise DataFetchError("Sample size (N) not found in text.")
    return int(match.group(1))

# ----------------------------------------------------------------------
# Effect size extraction
# ----------------------------------------------------------------------
# Cohen's d:   Cohen's d = 0.45   or   d = 0.45
_COHEN_D_RE = re.compile(
    r"Cohen['’]s?\s*d\s*=?\s*([-\d\.]+)", re.IGNORECASE
)

# F‑statistic: F(2, 145) = 4.5   (captures df1, df2, value)
_F_STAT_RE = re.compile(
    r"F\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*=?\s*([-\d\.]+)", re.IGNORECASE
)

def extract_effect_size(
    text: str,
) -> Tuple[float, str, Optional[Tuple[int, int]]]:
    """
    Extract an effect size from ``text``.

    The function first attempts to find a Cohen's *d* value; if that fails
    it looks for an ``F`` statistic.  The return tuple consists of:

    * ``value`` – the numeric effect size (Cohen's d or raw F value)
    * ``metric_type`` – either ``"Cohen's d"`` or ``"F"``
    * ``degrees_of_freedom`` – ``None`` for d, otherwise ``(df1, df2)``

    Parameters
    ----------
    text:
        The raw text to scan.

    Returns
    -------
    tuple
        ``(value, metric_type, degrees_of_freedom)``

    Raises
    ------
    DataFetchError
        If neither a Cohen's d nor an F statistic can be located.
    """
    # Try Cohen's d first.
    match_d = _COHEN_D_RE.search(text)
    if match_d:
        try:
            value = float(match_d.group(1))
        except ValueError as exc:
            raise DataFetchError("Invalid numeric value for Cohen's d.") from exc
        return value, "Cohen's d", None

    # Try F statistic.
    match_f = _F_STAT_RE.search(text)
    if match_f:
        try:
            df1 = int(match_f.group(1))
            df2 = int(match_f.group(2))
            value = float(match_f.group(3))
        except ValueError as exc:
            raise DataFetchError("Invalid numeric values in F statistic.") from exc
        return value, "F", (df1, df2)

    raise DataFetchError("No supported effect size pattern found in text.")
