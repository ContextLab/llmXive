"""
Unit normalization utilities for HEA yield strength data.

Provides conversion functions to standardize yield strength values to MPa.
"""

from typing import Union

import numpy as np

# Supported source units
SUPPORTED_UNITS = {"MPa", "GPa", "Pa", "psi", "ksi"}

def convert_yield_strength(
    value: Union[float, np.ndarray],
    source_unit: str,
    target_unit: str = "MPa",
) -> Union[float, np.ndarray]:
    """
    Convert yield strength values to a target unit (default: MPa).

    Parameters
    ----------
    value : float or np.ndarray
        The yield strength value(s) to convert.
    source_unit : str
        The unit of the input value. Must be one of SUPPORTED_UNITS.
    target_unit : str
        The desired output unit. Defaults to 'MPa'.

    Returns
    -------
    float or np.ndarray
        The converted value(s).

    Raises
    ------
    ValueError
        If source_unit or target_unit is not supported.
    """
    source_unit = source_unit.upper()
    target_unit = target_unit.upper()

    if source_unit not in SUPPORTED_UNITS:
        raise ValueError(
            f"Unsupported source unit: {source_unit}. "
            f"Supported units: {SUPPORTED_UNITS}"
        )
    if target_unit not in SUPPORTED_UNITS:
        raise ValueError(
            f"Unsupported target unit: {target_unit}. "
            f"Supported units: {SUPPORTED_UNITS}"
        )

    # Conversion factors to MPa
    to_mpa = {
        "MPa": 1.0,
        "GPa": 1000.0,
        "Pa": 1e-6,
        "psi": 0.00689476,
        "ksi": 6.89476,
    }

    # Convert source to MPa, then MPa to target
    value_in_mpa = np.asarray(value, dtype=float) * to_mpa[source_unit]

    if target_unit == "MPa":
        return value_in_mpa.item() if np.isscalar(value) else value_in_mpa

    # Convert from MPa to target
    from_mpa = {v: 1.0 / k for k, v in to_mpa.items()}
    result = value_in_mpa * from_mpa[target_unit]

    return result.item() if np.isscalar(value) else result

def normalize_to_mpa(
    value: Union[float, np.ndarray],
    source_unit: str,
) -> Union[float, np.ndarray]:
    """
    Normalize a yield strength value to MPa.

    Convenience wrapper around convert_yield_strength with target_unit='MPa'.

    Parameters
    ----------
    value : float or np.ndarray
        The yield strength value(s) to convert.
    source_unit : str
        The unit of the input value.

    Returns
    -------
    float or np.ndarray
        The value in MPa.
    """
    return convert_yield_strength(value, source_unit, target_unit="MPa")
