"""Utility package.

Centralises small helper functions that are reused across the code base.
"""

# Export metric utilities
from .metrics import entropy, log_prob_shift  # noqa: F401

__all__ = [
    "entropy",
    "log_prob_shift",
]
