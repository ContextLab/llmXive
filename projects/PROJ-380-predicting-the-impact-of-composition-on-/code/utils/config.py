"""
Configuration module for the BMG Shear Modulus Prediction Pipeline.

This module provides:
- Random seed management for reproducibility across numpy, random, and torch (if available).
- Centralized path constants for the project directory structure.
- Directory initialization utilities.
"""

import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

# Project Root: Assumes this file is at code/utils/config.py
# We traverse up to find the project root (the directory containing 'code', 'data', etc.)
_CURRENT_FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE_PATH.parent.parent.parent

# --- Random Seed Constants ---
DEFAULT_SEED = 42
SEED_ENV_VAR = "BMG_PIPELINE_SEED"

# --- Path Constants ---
PATHS: Dict[str, Path] = {
    "root": PROJECT_ROOT,
    "code": PROJECT_ROOT / "code",
    "data": PROJECT_ROOT / "data",
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "data_artifacts": PROJECT_ROOT / "data" / "artifacts",
    "tests": PROJECT_ROOT / "tests",
    "docs": PROJECT_ROOT / "docs",
    "specs": PROJECT_ROOT / "specs",
    "state": PROJECT_ROOT / "state",
    "state_projects": PROJECT_ROOT / "state" / "projects",
    "figures": PROJECT_ROOT / "figures",
}


def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Sets the random seed for reproducibility across the pipeline.

    Args:
        seed: The seed value. If None, checks the BMG_PIPELINE_SEED environment variable,
              otherwise defaults to DEFAULT_SEED (42).

    Returns:
        The integer seed that was set.
    """
    if seed is None:
        env_seed = os.getenv(SEED_ENV_VAR)
        if env_seed is not None:
            try:
                seed = int(env_seed)
            except ValueError:
                seed = DEFAULT_SEED
        else:
            seed = DEFAULT_SEED

    # Set seed for Python's random module
    random.seed(seed)

    # Set seed for NumPy
    np.random.seed(seed)

    # Attempt to set seed for PyTorch if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # PyTorch not installed, ignore

    return seed


def get_paths() -> Dict[str, Path]:
    """
    Returns a dictionary of all defined project paths.

    Returns:
        A dictionary mapping path names to their absolute Path objects.
    """
    return PATHS.copy()


def ensure_directories() -> Dict[str, Path]:
    """
    Creates all required project directories if they do not exist.

    Returns:
        A dictionary of the created paths.
    """
    for path in PATHS.values():
        path.mkdir(parents=True, exist_ok=True)
    return PATHS.copy()


def main() -> None:
    """
    CLI entry point for the config module.
    Initializes directories and prints the seed configuration.
    """
    import argparse

    parser = argparse.ArgumentParser(description="BMG Pipeline Configuration Utility")
    parser.add_argument("--init", action="store_true", help="Initialize all project directories")
    parser.add_argument("--seed", type=int, default=None, help="Set a specific random seed")
    parser.add_argument("--show-paths", action="store_true", help="Print all resolved paths")

    args = parser.parse_args()

    if args.init:
        paths = ensure_directories()
        print(f"Initialized directories under: {paths['root']}")
        for name, p in paths.items():
            print(f"  - {name}: {p}")

    current_seed = set_random_seed(args.seed)
    print(f"Random seed set to: {current_seed}")

    if args.show_paths:
        for name, p in PATHS.items():
            print(f"{name}: {p}")


if __name__ == "__main__":
    main()