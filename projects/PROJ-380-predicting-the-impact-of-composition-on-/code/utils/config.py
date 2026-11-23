import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

# Project Root (assumed to be the parent of the 'code' directory)
# If run as a script, __file__ is code/utils/config.py
# If imported, we try to locate the project root dynamically.
_CURRENT_FILE = Path(__file__).resolve()
PROJECT_ROOT = _CURRENT_FILE.parent.parent.parent

# Constants for directory structure
DIRS: Dict[str, Path] = {
    "code": PROJECT_ROOT / "code",
    "data": PROJECT_ROOT / "data",
    "tests": PROJECT_ROOT / "tests",
    "docs": PROJECT_ROOT / "docs",
    "state": PROJECT_ROOT / "state",
    "artifacts": PROJECT_ROOT / "artifacts",
    "contracts": PROJECT_ROOT / "contracts",
    "raw": PROJECT_ROOT / "data" / "raw",
    "processed": PROJECT_ROOT / "data" / "processed",
    "figures": PROJECT_ROOT / "figures",
}

# Default Random Seed
DEFAULT_SEED = 42


def get_paths() -> Dict[str, Path]:
    """
    Returns a dictionary of absolute paths to key project directories.
    """
    return DIRS.copy()


def ensure_directories() -> None:
    """
    Creates all required project directories if they do not exist.
    """
    for path in DIRS.values():
        path.mkdir(parents=True, exist_ok=True)


def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Sets the random seed for reproducibility across Python, NumPy, and random modules.
    
    Args:
        seed: The seed value. If None, uses DEFAULT_SEED (42).
    
    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Note: If using torch/tensorflow, seeds would be set here too,
    # but per constraints we are on CPU-only and standard libraries.
    
    return seed


def main() -> None:
    """
    CLI entry point for configuration setup.
    Creates directories and prints the active configuration.
    """
    print("Initializing project configuration...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Set seed
    seed = set_random_seed()
    print(f"Random seed set to: {seed}")
    
    # Print paths
    paths = get_paths()
    print("\nProject Paths:")
    for name, path in paths.items():
        print(f"  {name}: {path}")
    
    print("\nConfiguration initialized successfully.")


if __name__ == "__main__":
    main()