"""
Runner script for T007: Setup state/projects/PROJ-345/ structure and state.yaml initialization.
This script initializes the project state directory and creates the initial state.yaml file.
"""
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from state_management import main as state_init_main


def main():
    """Entry point for the state initialization runner."""
    # Delegate to the main function in state_management
    return state_init_main()


if __name__ == "__main__":
    sys.exit(main())
