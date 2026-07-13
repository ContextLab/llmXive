"""
Runner script for mixed-effects analysis.

This script provides a convenient entry point to run the mixed-effects analysis
on the simulation logs. It handles argument parsing and execution flow.
"""

import os
import sys
import logging

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyze.mixed_effects import main

def main_entry():
    """Entry point for the runner script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return main()

if __name__ == "__main__":
    sys.exit(main_entry())
