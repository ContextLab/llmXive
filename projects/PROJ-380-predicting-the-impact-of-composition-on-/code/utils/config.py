import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

# Project root is assumed to be the parent of the 'code' directory
# or explicitly set via environment variable.
_PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).resolve().parents[2]))

def get_paths() -> Dict[str, Path]:
    """
    Returns a dictionary of key paths relative to the project root.
    
    Returns:
        Dict mapping logical keys to absolute Path objects.
    """
    base = _PROJECT_ROOT
    return {
        "root": base,
        "code": base / "code",
        "data": base / "data",
        "data_raw": base / "data" / "raw",
        "data_processed": base / "data" / "processed",
        "data_artifacts": base / "data" / "artifacts",
        "tests": base / "tests",
        "docs": base / "docs",
        "state": base / "state",
        "artifacts": base / "artifacts",
        "contracts": base / "contracts"
    }

def ensure_directories(paths: Optional[Dict[str, Path]] = None) -> None:
    """
    Ensures that all required directories exist.
    
    Args:
        paths: Optional dictionary of paths. If None, uses get_paths().
    """
    if paths is None:
        paths = get_paths()
    
    # Define directories to ensure
    dirs_to_create = [
        paths["data_raw"],
        paths["data_processed"],
        paths["data_artifacts"],
        paths["state"],
        paths["artifacts"],
        paths["contracts"]
    ]
    
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

def set_random_seed(seed: int = 42) -> None:
    """
    Sets random seeds for reproducibility across libraries.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    np.random.seed(seed)
    if hasattr(os, 'seed'):
        os.seed(seed)

def main():
    """CLI entry point for config utilities."""
    import argparse
    parser = argparse.ArgumentParser(description="Project Configuration Utilities")
    parser.add_argument("--ensure-dirs", action="store_true", help="Ensure all directories exist")
    parser.add_argument("--set-seed", type=int, default=42, help="Set random seed")
    args = parser.parse_args()

    if args.ensure_dirs:
        ensure_directories()
        print("Directories ensured.")
    
    if args.set_seed:
        set_random_seed(args.set_seed)
        print(f"Random seed set to {args.set_seed}.")

if __name__ == "__main__":
    main()
