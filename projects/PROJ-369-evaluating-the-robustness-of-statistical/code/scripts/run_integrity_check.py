"""
Script to run the data integrity check (T067).

This script verifies all processed files have valid checksums and match
the expected schema, producing data/results/integrity_report.json.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.integrity_checker import main as integrity_main

def main():
    """Run the integrity check."""
    integrity_main()

if __name__ == "__main__":
    main()
