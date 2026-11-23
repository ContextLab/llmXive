#!/usr/bin/env python3
"""
Script to initialize data directories with .gitkeep files.
This ensures the directory structure is preserved in git repositories.
"""

import os
import sys

# Add the project root to the path to allow importing code modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from code.setup_data_dirs import main

if __name__ == "__main__":
    main()