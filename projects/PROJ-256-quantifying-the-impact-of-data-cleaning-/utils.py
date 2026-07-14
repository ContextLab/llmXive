"""
Compatibility wrapper for utility functions.

The project’s scripts (e.g., `code/main.py`) import `setup_logging` and
`pin_random_seed` from a top‑level module named ``utils``.  The actual
implementations live in ``code/utils.py``.  To bridge this import path
without altering existing scripts, we re‑export the required symbols here.

This file is deliberately lightweight: it simply imports the concrete
implementations from ``code.utils`` and makes them available under the
expected top‑level module name.
"""

from code.utils import (
    pin_random_seed,
    compute_file_checksum,
    setup_logging,
)

__all__ = [
    "pin_random_seed",
    "compute_file_checksum",
    "setup_logging",
]