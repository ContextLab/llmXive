"""
Script to run the Sensitivity Analysis (Robustness Index) pipeline.

This script invokes the sensitivity analysis module to generate the
threshold variation table and write it to a CSV file.
"""

import sys
from pathlib import Path

# Add the project root to the path if running as a script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.stats.sensitivity import main

if __name__ == "__main__":
    sys.exit(main())
