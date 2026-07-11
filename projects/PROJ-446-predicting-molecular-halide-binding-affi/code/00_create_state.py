"""
Script to initialize the project state.yaml file and set up tracking hooks.
This script is the entry point for T011.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.utils.state_manager import init_project_state, get_project_state_path, update_artifact_hash
from code.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Initialize project state and register this script's output."""
    logger.info("Initializing project state for T011...")

    # Initialize the main state.yaml
    init_project_state()

    state_path = get_project_state_path()
    logger.info(f"State file created/updated at: {state_path}")

    # Register the state file itself as an artifact
    update_artifact_hash(state_path, "state.yaml", state_path)

    logger.info("T011 Complete: state.yaml tracking hooks established.")
    return 0


if __name__ == "__main__":
    sys.exit(main())