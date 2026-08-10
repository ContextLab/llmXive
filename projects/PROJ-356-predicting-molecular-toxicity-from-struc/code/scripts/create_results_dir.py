"""
Script to create the 'results' directory for the project.
This directory will store intermediate predictions, metrics, and analysis reports.
"""
import os
from pathlib import Path

def main():
    """
    Creates the results directory at the expected project location.
    """
    # Determine the project root relative to this script's location
    # Script is at: code/scripts/create_results_dir.py
    # Project root is: code/
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent.parent
    results_dir = code_dir / "results"

    if not results_dir.exists():
        results_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {results_dir}")
    else:
        print(f"Directory already exists: {results_dir}")

    # Ensure a .gitkeep file exists to preserve the directory in git
    gitkeep = results_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()
        print(f"Created .gitkeep in: {results_dir}")

if __name__ == "__main__":
    main()