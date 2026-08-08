"""
Script to execute Task T018: Aggregate and finalize trend results.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from analysis.generate_trend_results import main

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)