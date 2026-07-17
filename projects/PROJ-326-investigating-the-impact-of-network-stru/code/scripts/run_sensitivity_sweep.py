"""
Script to run sensitivity sweep analysis as part of the analysis pipeline.

This script is invoked by the run-book to generate the sensitivity sweep results.
"""

import sys
from pathlib import Path

# Add code directory to path
code_root = Path(__file__).parent.parent
sys.path.insert(0, str(code_root))

from code.src.analysis.sensitivity import main as sensitivity_main

if __name__ == "__main__":
    exit_code = sensitivity_main()
    sys.exit(exit_code)