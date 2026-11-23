"""
Seed management module.

This module provides a deterministic way to pin the random number generators
used throughout the project (the standard library ``random`` module and
NumPy's RNG).  The seed value is stored internally so that downstream code
can retrieve it via :func:`get_seed`.  Additionally, the seed is persisted
back into the project's configuration file (``code/config.yaml``) so that
the configuration reflects the actual seed used for a run, fulfilling
the requirement that the seed be stored in the config.

The implementation is deliberately lightweight and has no side‑effects
beyond setting the RNG states and updating the YAML config file.
It is safe to call ``pin_seeds`` multiple times – the most recent call
overwrites the stored seed.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Optional

import numpy as np
import yaml

from llmxive_toolkit import get_logger

# Initialise a logger for optional debugging output.
log = get_logger(__name__)

# Internal storage for the currently pinned seed.  ``None`` means that
# ``pin_seeds`` has not been called yet.
_current_seed: Optional[int] = None

# Path to the configuration file that holds the seed.  The file is
# expected to live alongside this module under ``code/config.yaml``.
_CONFIG_PATH = Path(__file__).with_name("config.yaml")


def _persist_seed_to_config(seed: int) -> None:
    """
    Persist the given ``seed`` into the YAML configuration file.

    If the file does not exist, it is created with a single ``seed`` entry.
    Existing keys are preserved; only the ``seed`` entry is overwritten.

    Parameters
    ----------
    seed : int
        The seed value to store.
    """
    config_data: dict = {}
    if _CONFIG_PATH.is_file():
        try:
            with _CONFIG_PATH.open("r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}
        except yaml.YAMLError as exc:
            log.error("Failed to read existing config.yaml: %s", exc)
            # Proceed with empty config; the write will overwrite the file.

    config_data["seed"] = seed
    try:
        with _CONFIG_PATH.open("w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f)
        log.info("Seed %s written to config file %s", seed, _CONFIG_PATH)
    except yaml.YAMLError as exc:
        log.error("Failed to write seed to config.yaml: %s", exc)
        raise


def pin_seeds(seed: int) -> None:
    """
    Pin the global random seeds.

    This function sets the seed for both the standard library ``random``
    module and NumPy's random generator to ``seed``.  The value is stored
    internally and can be retrieved later via :func:`get_seed`.  In
    addition, the seed is written back to the project's configuration
    file so that the configuration reflects the actual seed used.

    Parameters
    ----------
    seed : int
        The integer seed to use for deterministic execution.
    """
    global _current_seed
    _current_seed = seed

    # Pin the Python ``random`` module.
    random.seed(seed)

    # Pin NumPy's RNG.  NumPy respects the global seed via ``np.random.seed``.
    np.random.seed(seed)

    log.info("Global random seeds pinned to %s", seed)

    # Persist the seed into the YAML configuration.
    _persist_seed_to_config(seed)


def get_seed() -> int:
    """
    Return the seed that was most recently pinned.

    Raises
    ------
    RuntimeError
        If :func:`pin_seeds` has not been called yet.
    """
    if _current_seed is None:
        raise RuntimeError(
            "Seed has not been set. Call `pin_seeds(seed)` before requesting it."
        )
    return _current_seed
