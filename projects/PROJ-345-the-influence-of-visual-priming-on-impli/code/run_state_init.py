"""
Entry point script for initializing the state management system.
This script sets up the state.yaml file for Principle V (Versioning).
"""
import sys
from pathlib import Path

# Ensure the code directory is in the path
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from state_management import main

if __name__ == "__main__":
    main()
