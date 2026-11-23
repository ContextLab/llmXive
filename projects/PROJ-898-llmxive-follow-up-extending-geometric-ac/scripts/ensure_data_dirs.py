"""
Script to create data directory structure and .gitkeep files.
This script implements task T001c.
"""
import os
import sys

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from code.setup_data_dirs import main

if __name__ == '__main__':
    sys.exit(main())
