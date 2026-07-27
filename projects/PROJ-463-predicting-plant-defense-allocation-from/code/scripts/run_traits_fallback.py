"""
Script entry point for running T025b: Trait Fallback Data Fetch.

Usage:
    python scripts/run_traits_fallback.py
"""

import sys
from pathlib import Path

# Add code directory to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.data.traits_fallback import main

if __name__ == "__main__":
    main()
