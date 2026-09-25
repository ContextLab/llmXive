"""
Runner script to execute merge_results.py logic.
This script aggregates all JSONL files (baseline, hf_run_1b, hf_run_7b)
into a single data/results.csv (Single Source of Truth).
"""
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from analysis.merge_results import main

if __name__ == "__main__":
    main()