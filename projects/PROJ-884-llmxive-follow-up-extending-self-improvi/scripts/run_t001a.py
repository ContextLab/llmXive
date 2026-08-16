"""
Script to execute Task T001a: Create project directory structure.

This script runs the setup_structure.py module to create the required
directory tree for the llmXive project.
"""
import sys
from pathlib import Path

# Add the code directory to the path
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from setup_structure import main

if __name__ == "__main__":
    sys.exit(main())
