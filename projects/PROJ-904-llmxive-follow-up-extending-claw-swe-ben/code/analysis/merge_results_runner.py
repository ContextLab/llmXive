"""
Wrapper script to ensure merge_results.py is executed as a standalone command
and writes data/results.csv as required by T028.
This file is invoked by the run-book if merge_results.py is not directly callable
or to ensure the specific command structure required by the pipeline.
"""
import sys
from pathlib import Path

# Add parent to path to allow imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from analysis.merge_results import main

if __name__ == "__main__":
    sys.exit(main())