"""
code/config.py

Centralized configuration for paths, seeds, and hyperparameters.
This module ensures all components use consistent paths and settings.
"""

import os
import random
from pathlib import Path
from typing import List, Dict, Any, Optional

# DESIGN DECISION: Sequential baseline uses SAME PerceptionDLM model with context-reset (not LLaVA) to avoid architectural confounds. This overrides Spec FR-003 per Plan Summary and Complexity Tracking. See docs/design_decisions.md for formal record.

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
STATE_ROOT = PROJECT_ROOT / "state"
CODE_ROOT = PROJECT_ROOT / "code"

# Fixed Seeds for Reproducibility
RANDOM_SEED = 42
RANDOM_STATE = random.Random(RANDOM_SEED)

# Hyperparameters
TIPPING_POINT_THRESHOLD = 0.9  # Placeholder for scientific validation
BATCH_SIZE = 8

# Memory Constraints
MAX_MEMORY_MB = 7000  # 7GB

# Dataset Parameters
REGION_COUNTS = [10, 15, 20, 25, 30, 35, 40, 45, 50]
SAMPLES_PER_BIN = 50

def get_data_path(sub_path: Optional[str] = None) -> Path:
    """
    Get the absolute path to a location within the data directory.
    
    Args:
        sub_path: Optional sub-path relative to the data root.
        
    Returns:
        Absolute Path object.
    """
    if sub_path:
        return DATA_ROOT / sub_path
    return DATA_ROOT

def get_state_path(sub_path: Optional[str] = None) -> Path:
    """
    Get the absolute path to a location within the state directory.
    
    Args:
        sub_path: Optional sub-path relative to the state root.
        
    Returns:
        Absolute Path object.
    """
    if sub_path:
        return STATE_ROOT / sub_path
    return STATE_ROOT

def get_random_state() -> random.Random:
    """
    Get the global random state instance.
    
    Returns:
        A random.Random instance seeded with RANDOM_SEED.
    """
    return RANDOM_STATE

def ensure_directories(paths: Optional[List[Path]] = None) -> None:
    """
    Ensure that all required directories exist.
    
    This function is called by multiple modules (main.py, generator.py, etc.)
    with different argument signatures. It is designed to be tolerant:
    - Called with no args: ensures standard data/state dirs.
    - Called with a list of paths: ensures those specific paths.
    - Called with a single Path: ensures that path.
    
    Args:
        paths: Optional list or single Path object to ensure.
               If None, defaults to standard project directories.
    """
    dirs_to_create = []

    # Default directories if no specific paths provided
    if paths is None:
        dirs_to_create = [
            DATA_ROOT,
            DATA_ROOT / "raw",
            DATA_ROOT / "synthetic",
            DATA_ROOT / "processed",
            STATE_ROOT,
            CODE_ROOT / "synthetic",
            CODE_ROOT / "models",
            CODE_ROOT / "metrics",
            CODE_ROOT / "analysis",
        ]
    else:
        # Handle single path or list of paths
        if isinstance(paths, Path):
            dirs_to_create.append(paths)
        elif isinstance(paths, list):
            dirs_to_create.extend(paths)
        else:
            # Fallback for unexpected types, try to treat as path string
            try:
                dirs_to_create.append(Path(str(paths)))
            except Exception:
                pass

    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)

def main():
    """Test configuration loading and directory creation."""
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Root: {DATA_ROOT}")
    print(f"State Root: {STATE_ROOT}")
    print(f"Random Seed: {RANDOM_SEED}")
    print(f"Tipping Point Threshold: {TIPPING_POINT_THRESHOLD}")
    
    # Test directory creation
    ensure_directories()
    print("✓ Default directories ensured.")
    
    # Test with custom path
    custom_dir = DATA_ROOT / "test_custom"
    ensure_directories(custom_dir)
    assert custom_dir.exists(), "Custom directory creation failed"
    print("✓ Custom directory ensured.")

if __name__ == "__main__":
    main()