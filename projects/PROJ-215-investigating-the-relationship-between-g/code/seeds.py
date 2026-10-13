"""
seeds.py
---------
This script generates a deterministic random seed configuration file
``state/seeds.yaml`` containing integer seed values for the Python
``random`` module, NumPy, and optionally PyTorch (if the library is
available in the runtime environment).

The file is written using the project's ``paths`` helper from
``llmxive_toolkit`` which ensures the ``state`` directory exists.
The script can be executed directly::

    python code/seeds.py

and will create (or overwrite) ``state/seeds.yaml`` with the following
structure:

    random_seed: 42
    numpy_seed: 42
    torch_seed: 42   # only if ``torch`` is importable

The values are deliberately simple and reproducible, matching the
project's requirement for a single source of truth for random seeds.
"""

import json
import os
from pathlib import Path

import yaml  # PyYAML is part of the base environment
import random

import numpy as np

from llmxive_toolkit import paths, get_logger

# ----------------------------------------------------------------------
# Logger configuration
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Default seed values (chosen to be deterministic and simple)
# ----------------------------------------------------------------------
DEFAULT_SEED = 42


def _detect_torch_seed() -> int | None:
    """
    Attempt to import PyTorch and return a deterministic seed value.
    If PyTorch is not installed, return ``None`` so the caller can
    omit the ``torch_seed`` entry.

    Returns
    -------
    int | None
        The seed value for torch, or ``None`` if torch is unavailable.
    """
    try:
        import torch  # type: ignore
    except Exception as exc:  # pylint: disable=broad-except
        log.info("PyTorch not available – skipping torch_seed generation: %s", exc)
        return None

    # If torch is available we simply use the same deterministic seed.
    return DEFAULT_SEED


def _write_seeds_yaml(seed_dict: dict, output_path: Path) -> None:
    """
    Write the seed dictionary to ``output_path`` as a YAML file.

    Parameters
    ----------
    seed_dict : dict
        Mapping of seed names to integer values.
    output_path : pathlib.Path
        Destination file path. Parent directories are created if missing.
    """
    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Dump as YAML (preserve order for readability)
    with output_path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(seed_dict, f, sort_keys=False)

    log.info("Seed file written to %s", output_path)


def generate_seeds_yaml() -> Path:
    """
    Generate ``state/seeds.yaml`` with deterministic seeds.

    Returns
    -------
    pathlib.Path
        The path to the generated ``seeds.yaml`` file.
    """
    # Determine seeds
    seeds = {
        "random_seed": DEFAULT_SEED,
        "numpy_seed": DEFAULT_SEED,
    }

    torch_seed = _detect_torch_seed()
    if torch_seed is not None:
        seeds["torch_seed"] = torch_seed

    # Resolve the project‑relative path using the ``paths`` helper.
    # ``paths.path`` creates any missing intermediate directories.
    seeds_path = paths.path("state", "seeds.yaml")

    _write_seeds_yaml(seeds, seeds_path)

    return seeds_path


def _set_global_seeds(seed_dict: dict) -> None:
    """
    Apply the generated seeds to the global random generators.
    This function is optional but useful when this module is imported
    by downstream scripts.

    Parameters
    ----------
    seed_dict : dict
        Mapping containing at least ``random_seed`` and ``numpy_seed``.
    """
    random.seed(seed_dict["random_seed"])
    np.random.seed(seed_dict["numpy_seed"])

    if "torch_seed" in seed_dict:
        try:
            import torch  # type: ignore
            torch.manual_seed(seed_dict["torch_seed"])
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed_dict["torch_seed"])
        except Exception as exc:  # pylint: disable=broad-except
            log.warning("Failed to set torch seed: %s", exc)


def main() -> None:
    """
    Entry point for the script. Generates the seed file and
    synchronises the global RNGs.
    """
    seeds_path = generate_seeds_yaml()
    # Load the just‑written file to confirm contents and set globals.
    with seeds_path.open("r", encoding="utf-8") as f:
        seeds = yaml.safe_load(f)

    _set_global_seeds(seeds)

    log.info("Random seeds initialised: %s", seeds)


if __name__ == "__main__":
    main()
