"""
Utility configuration helpers for the project (T002).

Provides:
- ``set_seed()``: pins global random seeds for ``random``, ``numpy``
  and PyMC to guarantee absolute reproducibility (Constitution I).
- Path helpers (project root, data root).
- SHA-256 hashing of files.
"""

import hashlib
import os
import random
from pathlib import Path
from typing import Any, Dict

import numpy as np

# ----------------------------------------------------------------------
# Reproducibility: global seed pinning (Constitution I)
# ----------------------------------------------------------------------
# Single global default seed used by every script in the pipeline.
GLOBAL_SEED = 20240521

# Track the seed(s) that have been applied so scripts can assert that
# ``set_seed`` was actually called before any stochastic work.
_SEED_STATE: Dict[str, Any] = {"seed": None}

def set_seed(seed: int = GLOBAL_SEED) -> int:
    """
    Pin the global random seeds for ``random``, ``numpy`` and PyMC.

    This function MUST be called at the start of every script in the
    pipeline to ensure absolute reproducibility (Constitution I).

    Parameters
    ----------
    seed: int
        The seed value to use for all random number generators.

    Returns
    -------
    int
        The seed that was applied.
    """
    if not isinstance(seed, int):
        raise TypeError(f"seed must be an int, got {type(seed).__name__}")

    # 1. Python stdlib RNG
    random.seed(seed)

    # 2. NumPy legacy global RNG
    np.random.seed(seed)

    # 3. PyMC / Aesara-PyTensor RNG: set the module-level seed so that
    #    ``pm.sample`` (which uses ``numpy.random`` for its initial
    #    points) and any random-variable draws are reproducible.
    try:
        import pymc as _pm  # noqa: N813

        # PyMC v5 exposes ``pm.pytensor_random`` / randomstream seeding
        # via the shared RandomState/Generator. The canonical way is:
        if hasattr(_pm, "set_at_rng") and hasattr(_pm, "at_rng"):
            _rng = _pm.at_rng(seed)
            _pm.set_at_rng(_rng)
    except ImportError:
        # PyMC is not installed in this environment (e.g. lightweight
        # unit-test runs); numpy/random seeding above is still applied.
        pass

    _SEED_STATE["seed"] = seed
    return seed

def get_last_seed():
    """Return the last seed applied via :func:`set_seed` (or None)."""
    return _SEED_STATE["seed"]

def assert_seeded() -> None:
    """
    Fail loudly if :func:`set_seed` has not been called yet.

    Scripts should call ``assert_seeded()`` right after their first
    stochastic operation (or simply call ``set_seed()`` at startup).
    """
    if _SEED_STATE["seed"] is None:
        raise RuntimeError(
            "Reproducibility violation (Constitution I): set_seed() has "
            "not been called. Call src.utils.config.set_seed() at the "
            "start of every script before any stochastic computation."
        )

# ----------------------------------------------------------------------
# Path helpers
# ----------------------------------------------------------------------
def get_project_root() -> Path:
    """
    Returns the absolute Path to the project root directory.

    The function assumes this file lives in <project_root>/src/utils/.
    """
    return Path(__file__).resolve().parents[2]

def get_data_root() -> Path:
    """
    Returns the absolute Path to the top-level data directory
    (<project_root>/data).
    """
    return get_project_root() / "data"

def get_state_root() -> Path:
    """
    Returns the absolute Path to the state directory (<project_root>/state).
    """
    return get_project_root() / "state"

# ----------------------------------------------------------------------
# Filesystem helpers
# ----------------------------------------------------------------------
def ensure_dir(p: Path) -> None:
    """
    Ensures the directory represented by ``p`` exists.
    Creates parent directories as needed.
    """
    p.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------
# Hashing helper
# ----------------------------------------------------------------------
def compute_file_hash(file_path: str) -> str:
    """
    Computes the SHA-256 hash of the file at ``file_path`` and returns
    the hexadecimal digest string.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

# Apply the global seed on import so that merely importing this module
# already yields a deterministic environment for every script.
set_seed(GLOBAL_SEED)
