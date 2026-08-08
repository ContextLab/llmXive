"""
Script to execute Task T016: Bootstrapping for Confidence Intervals.
This script runs the bootstrapping analysis and verifies the output.
"""
import sys
from pathlib import Path

# Add the code directory to the path so we can import analysis modules
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from analysis.bootstrapping import main

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
