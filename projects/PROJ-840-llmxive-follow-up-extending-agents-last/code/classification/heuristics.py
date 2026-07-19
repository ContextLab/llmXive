"""
Normalization Protocol Module.

Implements deterministic normalization of state data per FR-001:
- Float tolerance: EXACTLY 1e-6 (hardcoded, not configurable)
- Timestamp/ID stripping: replaces with canonical placeholders
- Reference canonicalization: replaces memory refs with canonical placeholder
"""
from typing import Any, Dict, Union
import re
from pathlib import Path
import math

# FR-001 Compliance: Float tolerance MUST be exactly 1e-6.
# Hardcoded to prevent configuration drift or accidental override.
FLOAT_TOLERANCE = 1e-6
DECIMAL_PLACES = 6  # Derived from 1e-6

# Canonical placeholders for stripping volatile data
TIMESTAMP_PLACEHOLDER = "[TIMESTAMP]"
ID_PLACEHOLDER = "[ID]"
REF_PLACEHOLDER = "[REF]"

# Regex patterns for identification
# ISO 8601 timestamps with optional timezone and fractional seconds
TIMESTAMP_PATTERN = r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?\b"
# UUIDs (case insensitive)
UUID_PATTERN = r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b"
# Memory references (hex addresses)
REFERENCE_PATTERN = r"\b0x[0-9a-fA-F]+\b"

# Pre-compile patterns for performance
_TIMESTAMP_RE = re.compile(TIMESTAMP_PATTERN)
_UUID_RE = re.compile(UUID_PATTERN, re.IGNORECASE)
_REFERENCE_RE = re.compile(REFERENCE_PATTERN)


def normalize_state(state: Union[Dict, str, float, int, None, list, tuple]) -> Any:
    """
    Recursively normalizes a state object to ensure deterministic comparison.

    Per FR-001:
    1. Floats are rounded to exactly 6 decimal places (tolerance 1e-6).
    2. Timestamps are replaced with '[TIMESTAMP]'.
    3. UUIDs/IDs are replaced with '[ID]'.
    4. Memory references (0x...) are replaced with '[REF]'.

    Args:
        state: The state object to normalize (can be dict, list, str, number, or None).

    Returns:
        The normalized state object.
    """
    if state is None:
        return None

    if isinstance(state, float):
        # FR-001: Enforce exact 1e-6 tolerance by rounding to 6 decimal places
        return round(state, DECIMAL_PLACES)

    if isinstance(state, int):
        return state

    if isinstance(state, str):
        # Strip timestamps
        normalized = _TIMESTAMP_RE.sub(TIMESTAMP_PLACEHOLDER, state)
        # Strip UUIDs/IDs
        normalized = _UUID_RE.sub(ID_PLACEHOLDER, normalized)
        # Strip memory references
        normalized = _REFERENCE_RE.sub(REF_PLACEHOLDER, normalized)
        return normalized

    if isinstance(state, dict):
        return {k: normalize_state(v) for k, v in state.items()}

    if isinstance(state, (list, tuple)):
        return [normalize_state(item) for item in state]

    # Fallback for other types (e.g., bool, custom objects)
    return state