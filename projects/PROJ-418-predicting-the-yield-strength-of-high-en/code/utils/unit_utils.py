"""
code/utils/unit_utils.py
------------------------

Conversion utilities for yield‑strength units.  The module defines
the public symbols required by the unit‑tests:

  - SUPPORTED_UNITS: list of recognised unit strings (case‑insensitive)
  - convert_yield_strength(value, source_unit, target_unit)
  - normalize_to_mpa(value, source_unit)

All conversions are performed via a simple factor‑to‑MPa mapping.
"""
import numpy as np
from typing import Union, List

# ----------------------------------------------------------------------
# Public constants
# ----------------------------------------------------------------------
SUPPORTED_UNITS: List[str] = ["MPa", "GPa", "Pa", "psi", "ksi"]

# Mapping from unit (lower‑cased) to a factor that converts the value
# to MPa.
_TO_MPA = {
    "mpa": 1.0,
    "gpa": 1000.0,
    "pa": 1e-6,
    "psi": 0.00689476,
    "ksi": 6.89476,
}

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _normalise_unit(unit: str) -> str:
    """
    Normalise a unit string to lower‑case and validate it.

    Raises
    ------
    ValueError
        If the unit is not in :data:`SUPPORTED_UNITS`.
    """
    unit_lc = unit.strip().lower()
    if unit_lc not in _TO_MPA:
        raise ValueError(f"Unsupported unit: {unit!r}")
    return unit_lc

def convert_yield_strength(
    value: Union[float, int, np.ndarray],
    source_unit: str,
    target_unit: str,
) -> Union[float, int, np.ndarray]:
    """
    Convert ``value`` from ``source_unit`` to ``target_unit``.

    The conversion is performed via MPa as an intermediate step:
    ``value * factor(source) / factor(target)``.

    Parameters
    ----------
    value :
        Numeric scalar or NumPy array.
    source_unit, target_unit :
        Unit strings; case‑insensitive.  Must be one of
        ``SUPPORTED_UNITS``.

    Returns
    -------
    Same type as ``value`` (scalar or ``np.ndarray``) containing the
    converted numbers.

    Raises
    ------
    ValueError
        If either unit is unsupported.
    """
    src = _normalise_unit(source_unit)
    tgt = _normalise_unit(target_unit)

    factor_src = _TO_MPA[src]
    factor_tgt = _TO_MPA[tgt]

    # Preserve the input type.
    if isinstance(value, np.ndarray):
        return (value * factor_src) / factor_tgt
    else:
        return (float(value) * factor_src) / factor_tgt

def normalize_to_mpa(value: Union[float, int, np.ndarray], source_unit: str) -> Union[float, int, np.ndarray]:
    """
    Convenience wrapper that converts ``value`` to MPa.

    Parameters
    ----------
    value :
        Numeric scalar or NumPy array.
    source_unit :
        Unit string (case‑insensitive) from :data:`SUPPORTED_UNITS`.

    Returns
    -------
    Converted value in MPa.
    """
    return convert_yield_strength(value, source_unit, "MPa")
