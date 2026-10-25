"""
Script to create the required project directory hierarchy.
Executes the equivalent of:
    mkdir -p src/data src/models src/analysis src/config src/utils \
    tests/contract tests/integration tests/unit
"""

import os
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def create_directories():
    """
    Create the directory structure required for the project.
    Uses llmxive_toolkit.paths to ensure folders are created inside the project root.
    """
    # List of directory specifications relative to the project root
    dirs = [
        ("src", "data"),
        ("src", "models"),
        ("src", "analysis"),
        ("src", "config"),
        ("src", "utils"),
        ("tests", "contract"),
        ("tests", "integration"),
        ("tests", "unit"),
    ]

    for parts in dirs:
        # paths.path creates the full Path and ensures the parent directories exist
        dir_path = paths.path(*parts)
        dir_path.mkdir(parents=True, exist_ok=True)
        log.info(f"Created directory: {dir_path}")

def main():
    """Entry point for the script."""
    create_directories()
    log.info("Project directory hierarchy created successfully.")

if __name__ == "__main__":
    main()