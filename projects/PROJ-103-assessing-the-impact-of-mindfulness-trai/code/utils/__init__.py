"""
Utility package for the mindfulness‑DMN analysis pipeline.

The public API re‑exports the seeding utilities so that they can be imported
as ``from src.utils import seeding`` (the test suite expects this layout).
"""
from .seeding import (
    DEFAULT_SEED,
    TORCH_AVAILABLE,
    set_all_seeds,
    get_seed,
    verify_determinism,
)
