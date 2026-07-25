"""
Setup script for PROJ-003-single-cell-trajectories-of-t-cell-exhau.
Creates the required directory structure for data and tests.
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIRS = [
    "data/raw",
    "data/processed",
    "data/results",
]

# Test directories
TEST_DIRS = [
    "tests/unit",
    "tests/integration",
]

def setup_directories():
    """Create all required directories if they do not exist."""
    all_dirs = DATA_DIRS + TEST_DIRS
    created_count = 0

    for dir_path in all_dirs:
        full_path = PROJECT_ROOT / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"\nSetup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    setup_directories()
