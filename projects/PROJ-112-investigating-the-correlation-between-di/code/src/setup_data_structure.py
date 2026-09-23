import os
import sys
from pathlib import Path
import argparse
import logging
from src.utils.logger import get_logger


def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the project root is two levels up from this file (code/src/).
    """
    current_file = Path(__file__).resolve()
    # Navigate up from code/src/setup_data_structure.py to project root
    return current_file.parent.parent


def setup_directories(project_root: Path = None) -> None:
    """
    Create the required directory structure for the project.
    Includes data, state, docs, and code structure as per T001 and T008.

    Args:
        project_root: Path to the project root. If None, auto-detects.
    """
    if project_root is None:
        project_root = get_project_root()

    logger = get_logger("setup_data_structure")
    logger.info(f"Setting up directory structure at: {project_root}")

    # Define all required directories relative to project root
    directories = [
        # Data directories (T008 specific)
        "data/raw",
        "data/processed",
        "data/processed/results",

        # State and docs
        "state",
        "docs",

        # Code structure (T001 specific)
        "code/src",
        "code/src/ingestion",
        "code/src/preprocessing",
        "code/src/analysis",
        "code/src/utils",

        # Test structure
        "code/tests",
        "code/tests/contract",
        "code/tests/integration",
        "code/tests/unit",
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")

    logger.info(f"Directory setup complete. Created {created_count} new directories.")


def build_arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description="Setup the project directory structure."
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Path to the project root. If not provided, auto-detected."
    )
    return parser


def main() -> int:
    """
    Main entry point for the script.
    Returns 0 on success, 1 on failure.
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    try:
        project_root = Path(args.project_root) if args.project_root else None
        setup_directories(project_root)
        return 0
    except Exception as e:
        logging.error(f"Failed to setup directories: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())