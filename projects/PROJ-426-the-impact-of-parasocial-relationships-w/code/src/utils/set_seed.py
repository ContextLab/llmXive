"""
Utility to set a global random seed for reproducibility across the pipeline.

This script:
1. Sets the seed for Python's ``random`` module, NumPy, and (if installed) PyTorch.
2. Writes the seed value to ``config/random_seed.yaml`` so that downstream
   components can read the canonical seed.
3. Provides a ``set_global_seed`` function that can be imported by any
   downstream script that needs deterministic behaviour.
"""

import random
from pathlib import Path

import numpy as np
import yaml
from llmxive_toolkit import paths, get_logger

# Optional import – the environment may not have torch installed.
try:
    import torch
    _HAS_TORCH = True
except Exception:  # pragma: no cover
    _HAS_TORCH = False

log = get_logger(__name__)

# Default seed as required by the task specification
DEFAULT_SEED = 42

# Path where the seed configuration will be stored
SEED_CONFIG_PATH = paths.config("random_seed.yaml")


def _write_seed_file(seed: int) -> None:
    """
    Write the seed value to ``config/random_seed.yaml``.  The file is created
    if it does not exist; its parent directory is created on demand.
    """
    SEED_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SEED_CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump({"seed": seed}, f)
    log.info(f"Random seed ({seed}) written to {SEED_CONFIG_PATH}")


def set_global_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set the global random seed for deterministic execution.

    The function seeds:
    * ``random`` – the Python standard library RNG
    * ``numpy``  – NumPy's RNG
    * ``torch``  – PyTorch's RNG (if PyTorch is available)

    After seeding, the seed value is persisted to
    ``config/random_seed.yaml`` so that any downstream component can read the
    canonical seed.

    Parameters
    ----------
    seed : int, optional
        The seed to use.  Defaults to ``42`` as required by the task.
    """
    # Seed the standard library RNG
    random.seed(seed)
    log.debug(f"Python random seeded with {seed}")

    # Seed NumPy RNG
    np.random.seed(seed)
    log.debug(f"NumPy random seeded with {seed}")

    # Seed PyTorch RNG if the library is present
    if _HAS_TORCH:
        torch.manual_seed(seed)
        log.debug(f"PyTorch CPU RNG seeded with {seed}")
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            log.debug(f"PyTorch CUDA RNG seeded with {seed}")

    # Persist the seed to disk for downstream consumption
    _write_seed_file(seed)


def get_seed() -> int:
    """
    Retrieve the seed from ``config/random_seed.yaml``.  If the file does not
    exist, the default seed (42) is returned.

    Returns
    -------
    int
        The seed stored in the configuration file.
    """
    if SEED_CONFIG_PATH.is_file():
        try:
            with open(SEED_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return int(data.get("seed", DEFAULT_SEED))
        except Exception as e:  # pragma: no cover
            log.warning(f"Failed to read seed from {SEED_CONFIG_PATH}: {e}")
    return DEFAULT_SEED


def main() -> None:
    """
    Entry‑point used when the script is executed directly:

    ``python -m src.utils.set_seed``
    """
    set_global_seed()
    log.info("Global random seed initialisation complete.")


if __name__ == "__main__":
    main()
