"""
Thin wrapper that imports ``src.config`` and calls ``set_seed()`` at import time.
This guarantees that any module importing ``src.seed`` automatically seeds the
global random number generators.
"""

from .config import set_seed

# Seed as soon as this module is imported
set_seed()