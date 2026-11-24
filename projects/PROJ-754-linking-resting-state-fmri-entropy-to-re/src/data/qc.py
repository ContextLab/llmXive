"""
Thin wrapper that re‑exports the QC utilities from the real implementation.

Tests import ``src.data.qc``; this file simply forwards the public functions.
"""

from code.src.data.qc import (
    validate_and_filter,
    main,
)

__all__ = ["validate_and_filter", "main"]
