"""
CLI wrapper script to set up the data directory structure.

Usage:
    python scripts/setup_data.py
"""
import sys
import os

# Add the project root to the path to allow importing from code/
# This script is in scripts/, so we go up one level to get root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from code.setup_data_dirs import main

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
