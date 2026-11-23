"""
utils/data_loader.py
--------------------
Top‑level wrapper for pre‑flight URL verification.

The original implementation lives in ``code/utils/data_loader.py``. This
module re‑exports the same public function so that unit tests (which import
``utils.data_loader``) can locate it without requiring a package restructuring
of the existing codebase.
"""

from typing import List

# Import the core implementation from the existing module.
# Keeping a single source of truth avoids duplication.
from code.utils.data_loader import verify_urls  # noqa: F401

__all__ = ["verify_urls"]