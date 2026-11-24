"""
Utility functions for managing random seeds across the project.

This module provides a simple interface to set and retrieve the global
random seed used by the `random`, `numpy`, and `torch` libraries.  In
addition, the first time a seed is set the values are recorded to a
provenance file ``data/provenance/seeds.json`` so that downstream
tests (e.g. ``tests/unit/test_seed_pin.py``) can verify reproducibility.

The implementation is deliberately lightweight and has no side‑effects
beyond writing the provenance file once.  Subsequent calls to
:func:`set_seed` will update the RNGs but will *not* overwrite the JSON
file, preserving the original seed that was used at program start.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Optional

import numpy as np

# ``torch`` is an optional import because not every environment may have
# the CPU‑only build installed.  The rest of the project already depends on
# it, so we raise a clear error if it cannot be imported.
try:
    import torch
except Exception as exc:  # pragma: no cover
    raise ImportError("PyTorch is required for seed management but could not be imported") from exc

# ``llmxive_toolkit`` provides convenient path helpers that automatically
# create parent directories.
from llmxive_toolkit import paths

# ----------------------------------------------------------------------
# Internal state
# ----------------------------------------------------------------------
_global_seed: Optional[int] = None
_seed_file_written: bool = False

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def set_seed(seed: int) -> None:
    """
    Set the global random seed for ``random``, ``numpy`` and ``torch``.

    The first call also writes the seed values to
    ``data/provenance/seeds.json``.  Subsequent calls update the RNGs
    without altering the provenance file.

    Parameters
    ----------
    seed: int
        The seed value to use for all RNGs.
    """
    global _global_seed, _seed_file_written

    _global_seed = seed

    # Standard library RNG
    random.seed(seed)

    # NumPy RNG
    np.random.seed(seed)

    # PyTorch RNG – deterministic CPU behaviour
    torch.manual_seed(seed)
    # Ensure deterministic behaviour for operations that use CUDA even though we run on CPU.
    torch.use_deterministic_algorithms(True)

    # Write provenance file on first invocation.
    if not _seed_file_written:
        _write_seed_provenance(seed)
        _seed_file_written = True

def get_seed() -> Optional[int]:
    """
    Retrieve the currently configured global seed.

    Returns
    -------
    int or None
        The seed set by :func:`set_seed`, or ``None`` if no seed has been
        configured yet.
    """
    return _global_seed

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _write_seed_provenance(seed: int) -> None:
    """
    Write the seed values to ``data/provenance/seeds.json``.

    The JSON structure matches the expectations of the unit test
    ``test_seed_pin.py``:

    .. code-block:: json

        {
            "random_seed": 42,
            "numpy_seed": 42,
            "torch_seed": 42
        }

    Parameters
    ----------
    seed: int
        The seed value that was applied to all RNGs.
    """
    provenance_path = paths.data("provenance", "seeds.json")
    # ``paths.data`` ensures the directory exists.
    provenance_path.parent.mkdir(parents=True, exist_ok=True)

    seed_record = {
        "random_seed": seed,
        "numpy_seed": seed,
        "torch_seed": seed,
    }

    with provenance_path.open("w", encoding="utf-8") as fp:
        json.dump(seed_record, fp, indent=2, sort_keys=True)

    # No return value; the side‑effect is the creation of the file.