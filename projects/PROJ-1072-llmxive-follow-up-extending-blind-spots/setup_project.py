"""
Project Initialization Script for llmXive Pipeline (T001)

Creates the required directory structure per plan.md:
- code/ (source)
- tests/ (test suite)
- data/raw/, data/filtered/, data/traces/, data/results/, data/validation/ (data layers)
- specs/.../contracts/ (schema definitions)
- code/utils/ (shared utilities)

Also initializes __init__.py files to make directories Python packages.
"""
import os
import sys
from pathlib import Path

def ensure_dir(path: Path):
    """Create directory if it doesn't exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory exists: {path}")

def init_package(path: Path):
    """Create __init__.py in a directory to make it a package."""
    init_file = path / "__init__.py"
    if not init_file.exists():
        init_file.touch()
        print(f"Initialized package: {init_file}")
    else:
        print(f"Package already initialized: {init_file}")

def main():
    root = Path.cwd()
    
    # Core directories
    dirs = [
        root / "code",
        root / "tests",
        root / "data" / "raw",
        root / "data" / "filtered",
        root / "data" / "traces",
        root / "data" / "results",
        root / "data" / "validation",
        root / "specs" / "001-blind-spots-order-analysis" / "contracts",
        root / "code" / "utils",
    ]
    
    print("Initializing llmXive project structure...")
    for d in dirs:
        ensure_dir(d)
    
    # Initialize Python packages
    packages = [root / "code", root / "tests", root / "code" / "utils"]
    for p in packages:
        init_package(p)
    
    # Initialize data contract directories
    init_package(root / "specs" / "001-blind-spots-order-analysis" / "contracts")
    
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()