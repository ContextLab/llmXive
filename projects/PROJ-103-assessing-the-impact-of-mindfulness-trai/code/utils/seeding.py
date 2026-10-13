"""
Thin wrapper exposing the same public API as ``src.utils.seeding`` at the
top‑level ``code.utils`` package.  This satisfies the “canonical layout”
requirement while keeping a single source of truth for the implementation.
"""

from ..src.utils.seeding import (
    DEFAULT_SEED,
    TORCH_AVAILABLE,
    set_all_seeds,
    get_seed,
    verify_determinism,
)
