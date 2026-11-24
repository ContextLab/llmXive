"""
Thin wrapper exposing the same public API as ``src.utils.seeding`` at the
top‑level ``code.utils`` package.
"""

from code.src.utils.seeding import (
    DEFAULT_SEED,
    set_all_seeds,
    get_seed,
    verify_determinism,
)
