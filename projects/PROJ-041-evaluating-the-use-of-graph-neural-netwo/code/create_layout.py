"""
Project layout creator for T001.

This script ensures that the required top‑level directories exist and
that each package directory contains an ``__init__.py`` file so that they
are recognised as Python packages. It is idempotent – running it multiple
times will not overwrite existing files.
"""

import os
from pathlib import Path

# List of top‑level directories that must exist
TOP_LEVEL_DIRS = [
    "code",
    "code/utils",
    "code/data",
    "code/models",
    "code/analysis",
    "data",
    "data/raw",
    "data/processed",
    "data/results",
    "docs",
    "tests",
]

# Directories that should be Python packages (need __init__.py)
PACKAGE_DIRS = [
    "code",
    "code/utils",
    "code/data",
    "code/models",
    "code/analysis",
    "tests",
]

def ensure_directories():
    """Create the required directories if they do not exist."""
    for d in TOP_LEVEL_DIRS:
        Path(d).mkdir(parents=True, exist_ok=True)

def ensure_init_files():
    """Create an empty __init__.py in each package directory."""
    for pkg in PACKAGE_DIRS:
        init_path = Path(pkg) / "__init__.py"
        if not init_path.exists():
            init_path.touch()

def main():
    ensure_directories()
    ensure_init_files()
    print("Project layout created successfully.")

if __name__ == "__main__":
    main()
