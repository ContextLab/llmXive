"""
Configuration utilities for the project.

This module provides a minimal yet functional implementation of the
configuration API expected by the rest of the codebase. It includes the
original public functions (`load_config`, `apply_random_seed`,
`enforce_runtime_limit`, `initialise_environment`) and adds a
compatibility wrapper `get_config` required by the collinearity check
script (`code/08_collinearity_check.py`).

The implementations are deliberately lightweight and avoid external
dependencies beyond the Python standard library and NumPy (which is
already a project dependency). They are sufficient for the execution
of the pipeline in a CI environment while preserving the original
contract for any existing callers.
"""

from __future__ import annotations

import json
import os
import random
import signal
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np

__all__ = [
    "load_config",
    "get_config",
    "apply_random_seed",
    "enforce_runtime_limit",
    "initialise_environment",
]


def load_config(config_path: str | os.PathLike = "config.json") -> Dict[str, Any]:
    """
    Load a JSON configuration file.

    Parameters
    ----------
    config_path : str or Path, optional
        Path to a JSON file containing configuration parameters.
        Defaults to ``'config.json'`` in the current working directory.

    Returns
    -------
    dict
        The parsed configuration dictionary. Returns an empty dict if the
        file does not exist or cannot be parsed.
    """
    path = Path(config_path)
    if not path.is_file():
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # In a production setting you might want to log this error.
        return {}


def get_config(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """
    Compatibility wrapper that mirrors the historic ``get_config`` API.

    The original implementation of the collinearity check script expects
    a function named ``get_config`` to return the configuration dictionary.
    Internally it simply forwards to :func:`load_config`, accepting any
    positional or keyword arguments for forward‑compatibility.
    """
    return load_config(*args, **kwargs)


def apply_random_seed(seed: int = 42) -> None:
    """
    Seed the random number generators used throughout the project.

    Parameters
    ----------
    seed : int, optional
        The seed value to set for ``random`` and ``numpy.random``. The
        default value ``42`` is used throughout the repository to ensure
        reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)

    # If other libraries (e.g., torch) are added later they can be seeded
    # here as well, guarded by import checks to keep this module lightweight.
    try:
        import torch  # type: ignore

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except Exception:
        # Torch is optional; ignore if not installed.
        pass


def enforce_runtime_limit(seconds: int = 3600) -> None:
    """
    Install a signal alarm to abort the process if it exceeds a time limit.

    Parameters
    ----------
    seconds : int, optional
        Maximum allowed runtime in seconds. Defaults to one hour (3600 s).
    """
    if not hasattr(signal, "SIGALRM"):
        # Windows does not support SIGALRM; simply return.
        return

    def _handler(signum: int, frame) -> None:  # pragma: no cover
        raise TimeoutError(f"Runtime limit of {seconds} seconds exceeded.")

    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)


def initialise_environment(seed: int = 42, runtime_limit: int = 3600) -> None:
    """
    Initialise the global execution environment.

    This convenience function applies the random seed and enforces the
    runtime limit. It is called by various entry‑point scripts to ensure
    a consistent environment across the pipeline.

    Parameters
    ----------
    seed : int, optional
        Random seed for reproducibility.
    runtime_limit : int, optional
        Maximum runtime in seconds.
    """
    apply_random_seed(seed)
    enforce_runtime_limit(runtime_limit)