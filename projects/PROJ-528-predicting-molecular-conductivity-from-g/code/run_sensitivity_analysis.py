import os
import sys
import json
import logging
import argparse
from typing import List, Dict, Any

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.analysis import run_sensitivity_analysis, main as analysis_main
from code.logging_config import setup_logging
from code.config import DATA_PATH

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Run sensitivity analysis pipeline.")
    parser.add_argument("--data", type=str, default="data/processed/descriptors.csv", help="Input descriptors CSV")
    parser.add_argument("--output", type=str, default="data/processed/sensitivity_analysis.json", help="Output JSON")
    args = parser.parse_args()

    # Ensure data exists
    if not os.path.exists(args.data):
        logging.error(f"Input file not found: {args.data}")
        sys.exit(1)

    # Run the analysis
    try:
        result = analysis_main() # analysis_main handles loading and saving
        print(f"Sensitivity analysis completed. Output: {args.output}")
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
