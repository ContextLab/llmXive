"""
Module to set up the project directory structure for the llmXive pipeline.
Creates required directories for raw data, processed data, results, and logs.
"""
import os
import sys
from pathlib import Path
import argparse
import logging
from src.utils.logger import get_logger

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes this script is located at code/src/setup_data_structure.py
    and project root is the parent of 'code'.
    """
    current_file = Path(__file__).resolve()
    # Navigate up from code/src/setup_data_structure.py -> code -> root
    project_root = current_file.parent.parent.parent
    return project_root

def setup_directories(root: Path, logger: logging.Logger) -> None:
    """
    Create the required directory structure for the project.
    
    Directories created:
    - data/raw/
    - data/processed/
    - data/processed/results/
    - logs/
    
    Args:
        root: The project root directory path.
        logger: Logger instance for status messages.
    """
    directories = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "processed" / "results",
        root / "logs",
        root / "state",
    ]

    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")

def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the script."""
    parser = argparse.ArgumentParser(
        description="Setup the project directory structure."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Path to the project root. If not provided, inferred from script location.",
    )
    return parser

def main(args: list = None) -> int:
    """
    Main entry point for the setup_data_structure script.
    
    Args:
        args: Command line arguments (defaults to sys.argv[1:]).
        
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = build_arg_parser()
    parsed_args = parser.parse_args(args)

    # Initialize logger
    logger = get_logger("setup_data_structure")

    try:
        root = Path(parsed_args.root) if parsed_args.root else get_project_root()
        
        if not root.exists():
            logger.error(f"Project root does not exist: {root}")
            return 1

        logger.info(f"Setting up directories in: {root}")
        setup_directories(root, logger)
        
        logger.info("Directory structure setup completed successfully.")
        return 0

    except Exception as e:
        logger.exception(f"Failed to setup directory structure: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())