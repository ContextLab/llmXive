"""
Script to set up the data directory structure for the project.
"""
import sys
import os

# Add the code directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_data_dirs import main

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)