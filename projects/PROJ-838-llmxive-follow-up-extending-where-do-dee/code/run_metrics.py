"""
Script to execute the metrics calculation batch process (T023).
This script is the entry point for the run-book to generate data/processed/metrics.csv.
"""
import sys
from pathlib import Path

# Add project root to path if necessary
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from metrics import main

if __name__ == "__main__":
    main()