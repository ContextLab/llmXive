"""
Script to initialize the data directory structure for the plant defense pipeline.

Usage:
    python scripts/setup_data_dirs.py

This script creates the following directories under the project's data root:
- data/raw
- data/processed
- data/traits
- data/manifests
- data/synthetic
"""
import sys
from pathlib import Path

# Ensure the code directory is in the path
code_root = Path(__file__).resolve().parents[1]
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from src.utils.setup_directories import main

if __name__ == "__main__":
    main()
