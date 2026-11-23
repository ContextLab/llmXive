"""
Analysis Entry Point for PROJ-015.

This script reconciles the run-book (quickstart.md) invocation `python code/analysis.py`
with the actual implementation located in `code/analysis/run_analysis.py`.

It serves as a shim that delegates to the full analysis pipeline, ensuring
the command specified in the quickstart works without duplicating logic.

Usage:
    python code/analysis.py --input data/raw --output data/processed --mode full
"""

import sys
import os

# Ensure the code directory is in the path so we can import analysis modules
# This handles cases where the script is run from the project root or code directory
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from analysis.run_analysis import main as run_analysis_main

def main():
    """
    Entry point for the analysis script.
    Delegates to the main function in code/analysis/run_analysis.py.
    """
    # Re-run the main entry point from the actual implementation
    # Pass sys.argv[1:] to preserve all CLI arguments intended for the underlying pipeline
    run_analysis_main()

if __name__ == "__main__":
    main()
