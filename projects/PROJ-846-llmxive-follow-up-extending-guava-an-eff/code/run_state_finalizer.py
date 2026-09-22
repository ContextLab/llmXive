"""
Task T044: Run state_manager to finalize project state hashes.

This script executes the state manager to scan the project directory,
calculate file hashes, and update the state YAML file at:
state/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml
"""

import os
import sys
from pathlib import Path

# Add project root to path to import utils
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.state_manager import main as state_manager_main
from utils.config import get_path


def main():
    """
    Entrypoint for T044.
    Initializes paths and runs the state manager update.
    """
    print("Starting T044: Finalizing project state hashes...")
    
    # Ensure the state directory exists
    state_dir = project_root / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize paths configuration to ensure get_path works correctly
    # The state_manager.py uses get_path internally, which relies on config initialization
    from utils.config import initialize_paths
    initialize_paths()
    
    # Run the state manager main logic
    # This scans files, calculates hashes, and writes the YAML atomically
    try:
        state_manager_main()
        print("T044 completed successfully. State file updated.")
    except Exception as e:
        print(f"T044 failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()