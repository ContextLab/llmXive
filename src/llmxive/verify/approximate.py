"""T008 — Precision-aware approximate comparison (spec 018, FR-002).

All functions are PURE and deterministic.  No network, no LLM calls.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PrecisionSpec:
    """Parsed precision information extracted from a claimed value string."""

    claimed: float    # numeric value
    decimals: int     # decimal places stated in the text
    sig_figs: int     # significant figures (meaningful for scientific/large values)
    hedge: bool       # a hedge word/symbol was present in the surrounding text


# ---------------------------------------------------------------------------
# Hedge detection
# ---------------------------------------------------------------------------

_HEDGE_PATTERNS = re.compile(
    r"\babout\b|\bapproximately\b|\broughly\b|\baround\b|~|≈",
    re.IGNORECASE,
)


def has_hedge(claim_text: str) -> bool:
    """Return True if *claim_text* contains a hedge word or approximation symbol."""
    return bool(_HEDGE_PATTERNS.search(claim_text))


# ---------------------------------------------------------------------------
# Precision parsing
# ---------------------------------------------------------------------------

_SCIENTIFIC_RE = re.compile(
    r"""
    (?P<mantissa>
        -?                        # optional sign
        \d+                       # integer part
        (?:\.(?P<frac>\d*))?      # optional fractional part
    )
    [eE]
    [+-]?\d+                      # exponent
    """,
    re.VERBOSE,
)

_DECIMAL_RE = re.compile(
    r"""
    (?P<integer>-?\d+)            # integer part
    (?:\.(?P<frac>\d+))?          # optional fractional digits
    """,
    re.VERBOSE,
)


def _count_sig_figs(mantissa: str) -> int:
    """Count significant figures in a mantissa string like '3' or '3.00'."""
    stripped = mantissa.lstrip("-").lstrip("0").replace(".", "")
    return len(stripped) or 1


def parse_precision(value_text: str) -> PrecisionSpec:
    """Parse the claimed numeric value and its stated precision from *value_text*.

    *value_text* should contain exactly one numeric token (e.g. "3.14",
    "3", "3.14159", "3.0e8").

    Returns a :class:`PrecisionSpec` with:
    - ``claimed``: the float value
    - ``decimals``: decimal places after the point (0 for integers)
    - ``sig_figs``: significant figures
    - ``hedge``: False (hedge is not embedded in the value text; use has_hedge
      on the full claim text)
    """
    text = value_text.strip()

    # Scientific notation takes priority
    m = _SCIENTIFIC_RE.search(text)
    if m:
        frac_part = m.group("frac") or ""
        mantissa = m.group("mantissa")
        sf = _count_sig_figs(mantissa)
        val = float(m.group(0))
        # decimals: number of decimal places in the *full* value would be huge;
        # for scientific notation we set decimals to the exponent-adjusted count
        # but in practice the caller uses sig_figs for these.
        return PrecisionSpec(
            claimed=val,
            decimals=len(frac_part),
            sig_figs=sf,
            hedge=False,
        )

    # Plain decimal / integer
    m = _DECIMAL_RE.search(text)
    if m:
        frac_part = m.group("frac") or ""
        decimals = len(frac_part)
        full_str = m.group("integer") + ("." + frac_part if frac_part else "")
        val = float(full_str)
        # sig figs: count non-leading-zero digits
        sf = _count_sig_figs(m.group("integer") + frac_part)
        return PrecisionSpec(claimed=val, decimals=decimals, sig_figs=sf, hedge=False)

    raise ValueError(f"No numeric token found in {value_text!r}")


# ---------------------------------------------------------------------------
# Rounding comparison
# ---------------------------------------------------------------------------

def is_valid_rounding(
    claimed: float,
    true_value: float,
    *,
    decimals: int,
    hedge: bool,
) -> bool:
    """Return True if *claimed* is a valid rounding of *true_value* to *decimals* places.

    Rules (FR-002):
    - Base: ``round(true_value, decimals) == claimed`` (numeric, ε-tolerant).
    - Hedge: also accept ``round(true_value, decimals-1)`` and
      ``round(true_value, decimals+1)`` (one extra place either way).

    Comparison is ALWAYS numeric — never substring.
    """
    def _close(a: float, b: float, d: int) -> bool:
        """Numeric equality with epsilon = 0.5 * 10**(-d) * 1e-6 relative tolerance."""
        # Primary: exact after rounding
        if round(true_value, d) == a:
            return True
        # Secondary: absolute epsilon for float noise
        epsilon = 0.5 * (10 ** -d) * 1e-6
        return abs(round(true_value, d) - a) < epsilon

    if _close(claimed, true_value, decimals):
        return True

    if hedge:
        # Accept one place coarser (decimals - 1, but not below 0)
        if decimals > 0 and _close(claimed, true_value, decimals - 1):
            return True
        # Accept one place finer (decimals + 1)
        if _close(claimed, true_value, decimals + 1):
            return True

    return False


# ---------------------------------------------------------------------------
# Correction formatting
# ---------------------------------------------------------------------------

def correction(true_value: float, *, decimals: int) -> str:
    """Format ``round(true_value, decimals)`` without a trailing ``.0``.

    Examples::

        correction(math.e, decimals=1)  -> "2.7"
        correction(math.pi, decimals=0) -> "3"
        correction(math.pi, decimals=2) -> "3.14"
    """
    rounded = round(true_value, decimals)
    if decimals <= 0:
        # Format as integer — no decimal point
        return str(int(rounded))
    # Format to exactly *decimals* places, then strip a spurious trailing zero
    # only when the value is a whole number (e.g. "3.0" → "3").
    formatted = f"{rounded:.{decimals}f}"
    # Remove trailing ".0" only when it is the sole fractional part
    if formatted.endswith(".0") and decimals == 1:
        # e.g. "3.0" when round(pi,0) but decimals=1 would be unusual; keep as "2.7"
        # Actually: if the result truly ends in ".0" with decimals==1, it's valid ("3.0"→"3")
        return formatted[:-2]  # strip ".0"
    # For decimals > 1: "3.10" is a valid representation; strip trailing zeros only
    # if the entire fractional part is zero (e.g. "5.00" → "5" when round gives integer)
    if "." in formatted:
        stripped = formatted.rstrip("0").rstrip(".")
        # Only use stripped form if the fractional part became empty (pure integer result)
        if "." not in stripped:
            return stripped
    return formatted


__all__ = [
    "PrecisionSpec",
    "correction",
    "has_hedge",
    "is_valid_rounding",
    "parse_precision",
]
