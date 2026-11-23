"""
Runner script for generating null model datasets.

This script generates random product states and Haar-random states
for comparative analysis (FR-010).
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from null_models import main

if __name__ == "__main__":
    main()
