#!/usr/bin/env python3
"""
Script to set up the data directory structure with .gitkeep files.

This script creates the required data subdirectories (raw, generated, results)
and ensures they are tracked by Git by placing .gitkeep files in them.
"""
import os
import sys

# Add the code directory to the path
code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'code')
sys.path.insert(0, code_dir)

from setup_data_dirs import main

if __name__ == "__main__":
    sys.exit(main())