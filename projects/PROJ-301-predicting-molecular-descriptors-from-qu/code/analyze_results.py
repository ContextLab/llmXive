"""
analyze_results.py: Entry point for analysis.

This script serves as the canonical entry point for the analysis logic
as referenced by the run-book and internal tests. It delegates to the implementation
in `code/04_analysis.py`.
"""

import sys
import os

# Ensure the code directory is in the path for relative imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the main logic from the implementation module
# Note: We use code_04_analysis because the file is named 04_analysis.py
# and Python converts hyphens/dots in imports differently.
from code_04_analysis import main as analysis_main

def main():
    """
    Entry point for the analyze_results command.
    Delegates execution to the analysis module.
    """
    print("Starting Analysis Pipeline (via code/analyze_results.py)...")
    try:
        analysis_main()
        print("Analysis completed successfully.")
    except Exception as e:
        print(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main()