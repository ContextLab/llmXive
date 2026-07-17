"""
Script to generate the data completeness report (T028).

This script executes the completeness reporter pipeline to analyze
the source distribution of the processed Heusler alloy dataset.
"""
import sys
from pathlib import Path

# Add project root to path if necessary
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.preprocessing.completeness_reporter import main

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
