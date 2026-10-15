"""
Simple regular‑expression based parsers used by the publication‑parsing stage.

Public symbols required by the test suite:
  - ``DataFetchError`` – custom exception raised when a pattern cannot be found.
  - ``extract_sample_size(text)`` – returns the integer *N* from a string like
    ``"N = 256"``.
  - ``extract_effect_size(text)`` – extracts either Cohen's *d* or an F‑statistic.
    Returns a tuple ``(value, metric_type, dof)`` where ``dof`` is ``None`` for
    Cohen's *d* and a ``(df1, df2)`` tuple for an F‑statistic.
"""
import re
from typing import Optional, Tuple

__all__ = ["DataFetchError", "extract_sample_size", "extract_effect_size"]

class DataFetchError(Exception):
    """Raised when a required pattern cannot be extracted from the input text."""
    pass

_SAMPLE_SIZE_REGEX = re.compile(r"N\s*=\s*(\d+)", flags=re.IGNORECASE)

def extract_sample_size(text: str) -> int:
    """
    Extract the sample size ``N`` from *text*.

    Parameters
    ----------
    text: str
        Input string that should contain a pattern like ``N = 123``.

    Returns
    -------
    int
        The extracted sample size.

    Raises
    ------
    DataFetchError
        If the pattern cannot be found.
    """
    match = _SAMPLE_SIZE_REGEX.search(text)
    if not match:
        raise DataFetchError("Sample size pattern not found")
    return int(match.group(1))

# Regex for Cohen's d – handles straight quotes, curly quotes, optional spaces
_COHEN_D_REGEX = re.compile(
    r"Cohen['’]s?\s*d\s*=?\s*([-\d\.]+)", flags=re.IGNORECASE
)

# Regex for F‑statistic with optional spaces: ``F(2, 145) = 4.5``
_FSTAT_REGEX = re.compile(
    r"F\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*=\s*([-\d\.]+)", flags=re.IGNORECASE
)

def extract_effect_size(text: str) -> Tuple[float, str, Optional[Tuple[int, int]]]:
    """
    Extract an effect size from *text*.

    The function looks for either a Cohen's *d* or an F‑statistic.  If a
    Cohen's *d* is found it returns ``(value, "Cohen's d", None)``.  If an
    F‑statistic is found it returns ``(value, "F", (df1, df2))``.  The first
    matching pattern wins.

    Parameters
    ----------
    text: str
        Input string containing the effect‑size expression.

    Returns
    -------
    tuple
        ``(effect_value, metric_type, dof)`` as described above.

    Raises
    ------
    DataFetchError
        If neither pattern can be found.
    """
    # Try Cohen's d first
    d_match = _COHEN_D_REGEX.search(text)
    if d_match:
        value = float(d_match.group(1))
        return (value, "Cohen's d", None)

    # Try F‑statistic
    f_match = _FSTAT_REGEX.search(text)
    if f_match:
        df1 = int(f_match.group(1))
        df2 = int(f_match.group(2))
        value = float(f_match.group(3))
        return (value, "F", (df1, df2))

    raise DataFetchError("Effect size pattern not found")
