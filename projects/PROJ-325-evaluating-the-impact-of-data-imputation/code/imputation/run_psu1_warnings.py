"""
Script to run T021: Write PSU=1 Warnings.

This script is invoked by the run-book to generate data/processed/psu1_warnings.json.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from imputation.psu1_warnings import main

if __name__ == "__main__":
    sys.exit(main())