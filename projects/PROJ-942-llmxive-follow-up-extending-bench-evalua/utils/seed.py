"""
Proxy module for the project's reproducibility seed helper.

The original implementation lives in ``code/utils/seed.py``.  This file
imports the real functions and constants and re‑exports them under the
top‑level ``utils`` package, satisfying test imports such as::

    from utils.seed import set_seeds

No additional logic is introduced – all behaviour (including the
deterministic NumPy value) is delegated to the original implementation.
"""

# Import the actual implementation from the code directory.
from importlib import import_module
import os
import sys
from pathlib import Path

# Ensure the repository's ``code`` directory is on ``sys.path``.
# This mirrors the logic used in ``code/pipelines/install_dependencies.py``.
_code_dir = Path(__file__).resolve().parents[1] / "code"
if str(_code_dir) not in sys.path:
    sys.path.insert(0, str(_code_dir))

# Load the original module.
_orig = import_module("utils.seed")  # This resolves to ``code/utils/seed.py`` after the path tweak.

# Re‑export the public API.
DEFAULT_SEED = getattr(_orig, "DEFAULT_SEED")
set_seeds = getattr(_orig, "set_seeds")
get_seed_state_summary = getattr(_orig, "get_seed_state_summary")

# Preserve the module's ``__all__`` for tidy imports.
__all__ = ["DEFAULT_SEED", "set_seeds", "get_seed_state_summary"]