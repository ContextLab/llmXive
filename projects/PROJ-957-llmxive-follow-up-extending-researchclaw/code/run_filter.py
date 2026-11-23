"""
Runner script for T008: Filter tasks by failure_mode.

This script executes the filter logic and writes the output files.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data.filter import main

if __name__ == "__main__":
    sys.exit(main())