"""
Script to explicitly create the project directory structure for PROJ-369.
This script creates all required directories as specified in T001.
"""
import os
import sys
from pathlib import Path

# Add the project root to the path if running directly
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.config import get_path, ensure_dirs
from src.utils.directory_manager import setup_project_directories, initialize_checksums
from src.utils.logging import setup_logger, log_info, log_error

def main():
    """
    Main entry point to create the project directory structure.
    """
    logger = setup_logger("setup_directories")
    log_info(logger, "Starting project directory setup...")

    # Define the required directory structure relative to project root
    required_dirs = [
        "src",
        "src/data",
        "src/synthesis",
        "src/analysis",
        "src/viz",
        "src/utils",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/raw",
        "data/processed",
        "data/results",
        "specs",
        "state",
    ]

    try:
        # Use the existing utility function to ensure directories exist
        # This leverages the config and ensure_dirs from utils
        project_root_path = get_path()
        created_count = 0

        for dir_name in required_dirs:
            dir_path = project_root_path / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
                log_info(logger, f"Created directory: {dir_path}")
            else:
                log_info(logger, f"Directory already exists: {dir_path}")

        log_info(logger, f"Project structure setup complete. {created_count} new directories created.")

        # Initialize checksums for the new structure if state directory exists
        state_dir = get_path("state")
        if state_dir.exists():
            log_info(logger, "Initializing checksums for project state...")
            initialize_checksums()
            log_info(logger, "Checksums initialized successfully.")

        return 0

    except Exception as e:
        log_error(logger, f"Error during directory setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())