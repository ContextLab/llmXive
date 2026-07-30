"""
CLI script to run the fallback trait data acquisition (T025b).

This script should be executed after T025a (traits_try.py) has completed
and identified species missing from the TRY database.

Usage:
    python scripts/run_traits_fallback.py
"""
import sys
from pathlib import Path

# Ensure project root is in path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.data.traits_fallback import main

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)