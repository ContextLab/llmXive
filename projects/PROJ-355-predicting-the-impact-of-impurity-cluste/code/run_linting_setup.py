import sys
import subprocess
from pathlib import Path

# Ensure we can import the config module
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_project_root
from config_linting import main as config_linting_main
from linting_setup import main as linting_setup_main

def main():
    """
    Orchestrates the setup of linting and formatting tools (ruff, black).
    This script is the entry point for T003.
    """
    print("Initializing linting and formatting configuration...")
    
    # 1. Run the linting configuration generator (creates pyproject.toml, .ruff.toml, etc.)
    config_linting_main()
    
    # 2. Run the tool installation/verification script
    # This ensures ruff and black are installed in the environment
    linting_setup_main()
    
    print("Linting and formatting configuration complete.")
    print("You can now run 'ruff check .' and 'black .' to validate the codebase.")

if __name__ == "__main__":
    main()
