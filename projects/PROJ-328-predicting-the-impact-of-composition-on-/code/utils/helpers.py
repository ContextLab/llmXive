"""
Helper utility functions for the solder hardness prediction pipeline.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import re

from config import get_composition_sum_threshold, get_max_elements

logger = logging.getLogger(__name__)

def ensure_dir(path_str: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path_str: Path string to ensure exists.

    Returns:
        Path object for the directory.
    """
    path = Path(path_str)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")
    return path

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float, returning default on failure.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        Float value or default.
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert '{value}' to float, using default {default}")
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int, returning default on failure.

    Args:
        value: Value to convert.
        default: Default value if conversion fails.

    Returns:
        Int value or default.
    """
    if value is None:
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        logger.warning(f"Failed to convert '{value}' to int, using default {default}")
        return default

def normalize_element_symbol(symbol: str) -> str:
    """
    Normalize an element symbol to standard chemical notation (e.g., 'sn' -> 'Sn').

    Args:
        symbol: Element symbol string.

    Returns:
        Normalized element symbol.
    """
    if not symbol:
        return ""
    # Handle common variations
    symbol = str(symbol).strip()
    if len(symbol) == 1:
        return symbol.upper()
    elif len(symbol) == 2:
        return symbol[0].upper() + symbol[1].lower()
    else:
        # Try to handle cases like 'Sb' or 'Ag' properly
        # If it's already valid, return as is; otherwise try standard capitalization
        return symbol[0].upper() + symbol[1:].lower()

def calculate_composition_sum(elemental_breakdown: Dict[str, float]) -> float:
    """
    Calculate the sum of elemental percentages in a composition.

    Args:
        elemental_breakdown: Dictionary of element:percentage.

    Returns:
        Sum of percentages.
    """
    if not elemental_breakdown:
        return 0.0
    total = 0.0
    for element, percentage in elemental_breakdown.items():
        total += safe_float(percentage, 0.0)
    return total

def validate_composition_threshold(
    elemental_breakdown: Dict[str, float],
    threshold: Optional[float] = None,
    max_elements: Optional[int] = None
) -> bool:
    """
    Validate that a composition meets the sum threshold and element count constraints.

    Args:
        elemental_breakdown: Dictionary of element:percentage.
        threshold: Minimum sum threshold (defaults to config value).
        max_elements: Maximum number of elements (defaults to config value).

    Returns:
        True if valid, False otherwise.
    """
    if threshold is None:
        threshold = get_composition_sum_threshold()
    if max_elements is None:
        max_elements = get_max_elements()

    # Check element count
    if len(elemental_breakdown) > max_elements:
        logger.debug(
            f"Composition has {len(elemental_breakdown)} elements, "
            f"exceeds max {max_elements}"
        )
        return False

    # Check sum threshold
    total = calculate_composition_sum(elemental_breakdown)
    if total < threshold:
        logger.debug(
            f"Composition sum {total:.2f} is below threshold {threshold}"
        )
        return False

    return True