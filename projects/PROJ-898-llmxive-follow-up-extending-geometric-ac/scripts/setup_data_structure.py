#!/usr/bin/env python3
"""
Script to initialize the project's data directory structure and ensure
.gitkeep files are present to track empty directories in version control.
"""
import sys
import os

# Add the code directory to the path if running from scripts/
current_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.join(current_dir, "..", "code")
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

from setup_data_dirs import main

if __name__ == "__main__":
    sys.exit(main())