import os
import sys
from pathlib import Path
from code.utils.state_manager import init_project_state, get_project_state_path, update_artifact_hash
from code.utils.logger import get_logger

def main():
    """
    Initialize the project state tracking system.
    Creates the initial state.yaml file in the project root.
    """
    logger = get_logger(__name__)
    project_root = Path("projects/PROJ-446-predicting-molecular-halide-binding-affi")

    if not project_root.exists():
        logger.error(f"Project root {project_root} does not exist.")
        return False

    # Initialize state
    state_path = get_project_state_path(project_root)
    logger.info(f"Initializing project state at: {state_path}")
    
    success = init_project_state(project_root)
    
    if success:
        logger.info("Project state initialized successfully.")
        # Update initial artifact hashes (empty set for now)
        update_artifact_hash(project_root)
        logger.info("Initial artifact hash updated.")
        return True
    else:
        logger.error("Failed to initialize project state.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)