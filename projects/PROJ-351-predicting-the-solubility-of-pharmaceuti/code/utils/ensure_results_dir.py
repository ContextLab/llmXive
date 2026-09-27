"""
Utility script to ensure the results directory exists and is writable.
Used by T048 to guarantee the log file path is valid before tests run.
"""
import os
from pathlib import Path

def ensure_results_directory():
    """Creates the results directory if it doesn't exist."""
    project_root = Path(__file__).parent.parent.parent
    results_dir = project_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir

if __name__ == "__main__":
    ensure_results_directory()
    print("Results directory ensured.")
