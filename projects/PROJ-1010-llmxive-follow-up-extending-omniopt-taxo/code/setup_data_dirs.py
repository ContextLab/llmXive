"""
Main entry point script to initialize the base data directory structure.

This script creates the required directories (data/raw, data/processed, etc.)
and initializes the state tracking file (data/state.json) and the empty
OmniOpt lookup table (data/omniopt_lookup.json).

Usage:
    python code/setup_data_dirs.py
"""
import sys
import os

# Add the code directory to the path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.insert(0, root_dir)

from utils.data_dirs import main

if __name__ == "__main__":
    main()
