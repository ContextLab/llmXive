"""
Script to initialize the project state file with checksums for initial artifacts.
This script is part of task T009 and should be run after Phase 2 setup tasks.
"""
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.state_manager import initialize_state_file


def main():
    """Main entry point for state initialization."""
    print("Initializing project state file with initial artifact checksums...")
    initialize_state_file()
    print("State initialization complete.")


if __name__ == "__main__":
    main()
