import logging
import sys
from pathlib import Path
from typing import List
import setup_project_structure

def create_directories(project_root: Path) -> None:
    """
    Delegate directory creation to the main setup script.
    """
    setup_project_structure.create_directories(project_root)

def main() -> None:
    """
    Main entry point for data directory setup.
    """
    logging.basicConfig(level=logging.INFO)
    project_root = setup_project_structure.get_project_root()
    create_directories(project_root)
    logging.info("Data directories created successfully.")

if __name__ == "__main__":
    main()
