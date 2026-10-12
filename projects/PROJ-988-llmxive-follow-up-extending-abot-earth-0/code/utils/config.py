"""
Configuration utilities for the ABot-Earth project.

This module provides:
- Loading of a city list from ``data/city_list.txt``.
- Deterministic random seed setting for ``random``, ``numpy`` and ``torch``.
- A simple ``get_config`` helper that returns the loaded city list and the seed in use.
"""

import os
import random
from pathlib import Path
from typing import List, Optional, Dict

import numpy as np

# ``torch`` may not be available in minimal environments, but it is a declared
# dependency of the project (used in other modules). Import lazily so the
# module can be imported even if the optional CUDA libraries are missing.
try:
    import torch
except Exception:  # pragma: no cover
    torch = None  # type: ignore

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_city_list(file_path: Optional[Path] = None) -> List[str]:
    """
    Load a list of city names from a plain‑text file.

    The default location is ``data/city_list.txt`` relative to the project
    root. Each line of the file should contain a single city name.

    Parameters
    ----------
    file_path: Path | None
        Custom path to the city list file. If ``None`` the default location
        is used.

    Returns
    -------
    List[str]
        List of city names stripped of surrounding whitespace. Empty lines
        are ignored.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    """
    if file_path is None:
        file_path = paths.data("city_list.txt")
    log.debug("Loading city list from %s", file_path)

    if not file_path.is_file():
        raise FileNotFoundError(f"City list file not found: {file_path}")

    with file_path.open("r", encoding="utf-8") as f:
        cities = [line.strip() for line in f if line.strip()]
    log.info("Loaded %d city names", len(cities))
    return cities

def set_random_seeds(seed: int = 42) -> None:
    """
    Set deterministic seeds for the Python random module, NumPy, and PyTorch.

    This function also sets the ``PYTHONHASHSEED`` environment variable to
    ensure reproducible hashing of strings across interpreter sessions.

    Parameters
    ----------
    seed: int
        The seed value to use. Defaults to ``42`` for reproducibility.
    """
    log.debug("Setting random seeds to %d", seed)

    # Python's built‑in random
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch (if available)
    if torch is not None:
        torch.manual_seed(seed)
        # Ensure deterministic behavior on CPU (no CUDA involved)
        torch.use_deterministic_algorithms(True)
        # For completeness, also set the CUDA seed even though CUDA should be unavailable
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

    # Environment variable for hash randomisation
    os.environ["PYTHONHASHSEED"] = str(seed)

    log.info("Random seeds set to %d", seed)

def get_config(seed: Optional[int] = None) -> Dict[str, object]:
    """
    Convenience helper that loads the city list and optionally sets the random seed.

    Parameters
    ----------
    seed: int | None
        If provided, ``set_random_seeds`` is called with this value. If ``None``,
        the default seed ``42`` is used.

    Returns
    -------
    dict
        Dictionary with keys:
        - ``city_list``: List[str] – the loaded city names.
        - ``seed``: int – the seed that was set.
    """
    if seed is None:
        seed = 42
    set_random_seeds(seed)
    city_list = load_city_list()
    config = {"city_list": city_list, "seed": seed}
    log.debug("Configuration prepared: %s", config)
    return config
