"""
Utility package initializer for the project.

This module re-exports the public I/O helper functions so that
``import code.utils`` provides direct access to the most commonly
used utilities without requiring the caller to know the exact sub‑module
layout.

The corrected version simply re‑exports everything that ``io.py`` defines
(including the checksum helpers that actually exist – e.g. ``sha256_checksum``).
"""
from .io import *  # noqa: F401,F403

__all__ = [name for name in globals() if not name.startswith('_')]