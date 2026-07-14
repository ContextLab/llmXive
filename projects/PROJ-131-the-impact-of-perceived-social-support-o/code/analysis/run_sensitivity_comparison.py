"""
Script to run the sensitivity comparison analysis (Task T028).

This script orchestrates the comparison of interaction coefficients between
baseline and sensitivity analysis results.
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.sensitivity_compare import main

if __name__ == "__main__":
    main()