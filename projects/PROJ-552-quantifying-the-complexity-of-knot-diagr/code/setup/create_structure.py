"""
Script to create the complete project directory structure.
Run this once to initialize all required directories.
"""
import os
from pathlib import Path

# Project root (assumed to be the parent of the code/ directory)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Directory structure to create
DIRECTORIES = [
    # Code packages
    "code/download",
    "code/data",
    "code/analysis",
    "code/reproducibility",
    # Data directories
    "data/raw",
    "data/processed",
    "data/plots",
    # Documentation
    "docs/reproducibility",
    # Specifications
    "specs/001-knot-complexity-analysis",
    # Test suites
    "tests/contract",
    "tests/integration",
    "tests/unit",
]

def create_structure():
    """Create all required directories."""
    created = []
    for dir_path in DIRECTORIES:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created.append(str(full_path.relative_to(PROJECT_ROOT)))
        print(f"Created: {full_path.relative_to(PROJECT_ROOT)}")

    print(f"\nTotal directories created: {len(created)}")
    return created

if __name__ == "__main__":
    create_structure()
