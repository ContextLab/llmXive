"""
Light‑weight parsers for extracting sample size and effect size information
from plain‑text fragments of scientific articles.
"""
import re
from typing import List, Optional, Tuple

class DataFetchError(Exception):
    """Raised when parsing fails to locate the required information."""

    pass

_SAMPLE_SIZE_RE = re.compile(r"N\s*=\s*(\d+)", re.IGNORECASE)

# Cohen's d patterns – accept straight quotes and typographic apostrophes.
_COHEN_D_RE = re.compile(
    r"Cohen['’]s?\s*d\s*=\s*([-\d\.]+)", re.IGNORECASE
)

# F‑statistic pattern with optional whitespace.
_F_STAT_RE = re.compile(
    r"F\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*=\s*([-\d\.]+)", re.IGNORECASE
)

def extract_sample_size(text: str) -> int:
    """
    Extract ``N`` (sample size) from *text*.

    The function looks for the pattern ``N = <integer>``.  If the pattern
    cannot be found a ``DataFetchError`` is raised.

    Parameters
    ----------
    text : str
        Input text.

    Returns
    -------
    int
        Sample size.

    Raises
    ------
    DataFetchError
        If no match is found.
    """
    match = _SAMPLE_SIZE_RE.search(text)
    if not match:
        raise DataFetchError("Sample size pattern not found")
    return int(match.group(1))

def extract_effect_size(
    text: str,
) -> Tuple[float, str, Optional[Tuple[int, int]]]:
    """
    Extract an effect size from *text*.

    Supports two metric types:
    - Cohen's d (e.g., ``Cohen's d = 0.45``)
    - F‑statistic (e.g., ``F(2, 145) = 4.5``)

    Returns
    -------
    tuple
        ``(value, metric_type, degrees_of_freedom)`` where
        ``degrees_of_freedom`` is ``None`` for Cohen's d and a ``(df1,
        df2)`` tuple for an F‑statistic.

    Raises
    ------
    DataFetchError
        If the text does not contain a recognised effect size.
    """
    # Try Cohen's d first.
    match = _COHEN_D_RE.search(text)
    if match:
        value = float(match.group(1))
        return (value, "Cohen's d", None)

    # Try F‑statistic.
    match = _F_STAT_RE.search(text)
    if match:
        df1 = int(match.group(1))
        df2 = int(match.group(2))
        value = float(match.group(3))
        return (value, "F", (df1, df2))

    raise DataFetchError("Effect size pattern not found")