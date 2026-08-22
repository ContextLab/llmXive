"""
Project initialization script for T001a.
Creates the required directory structure and generates the setup log.
"""
import os
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging

# Import shared utilities from utils.py as per API surface
from utils import get_logger, get_project_paths

# Ensure we can import from the code directory if run from root
# The API surface says `from utils import ...` works, so we assume PYTHONPATH is set or this runs from code/
# But to be safe for the runner which might execute `python code/setup_project.py`, we handle imports.
# The provided API surface for setup_project.py shows:
# imports: from utils import get_logger, get_project_paths
# So we trust that utils.py is in the same directory or path.

def create_directories(logger: logging.Logger) -> None:
    """
    Creates the required directory structure for the project.
    Directories: code/, data/raw/, data/processed/, data/reports/, tests/, state/, state/projects/
    """
    # Define relative paths from project root
    # Since this script lives in code/, we need to go up one level to get the root
    # However, the task says "in repository root".
    # If this script is run as `python code/setup_project.py`, we should resolve the root relative to this file.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state",
        "state/projects"
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

    logger.info(f"Total directories created/verified: {len(directories)}")

def verify_directories(logger: logging.Logger) -> bool:
    """
    Verifies that all required directories exist.
    Returns True if all exist, False otherwise.
    """
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state",
        "state/projects"
    ]

    all_exist = True
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            logger.error(f"Missing directory: {dir_path}")
            all_exist = False
        else:
            logger.debug(f"Verified directory: {dir_path}")

    return all_exist

def generate_setup_log(logger: logging.Logger) -> None:
    """
    Generates state/setup_log.txt with command output and timestamp.
    """
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    state_dir = project_root / "state"
    log_file = state_dir / "setup_log.txt"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    command_executed = "mkdir -p code/ data/raw/ data/processed/ data/reports/ tests/ state/ state/projects/"

    # Build the content
    content_lines = [
        f"T001a Project Setup Log",
        f"Timestamp: {timestamp}",
        f"Command Executed: {command_executed}",
        f"Project Root: {project_root}",
        f"----------------------------------------",
        f"Directory Creation Results:",
    ]

    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state",
        "state/projects"
    ]

    for dir_name in directories:
        dir_path = project_root / dir_name
        status = "EXISTS" if dir_path.exists() else "MISSING"
        content_lines.append(f"  {dir_name}: {status}")

    content_lines.append(f"----------------------------------------")
    content_lines.append(f"Verification: {'PASSED' if verify_directories(logger) else 'FAILED'}")

    # Write to file
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(content_lines) + '\n')

    logger.info(f"Setup log generated at: {log_file}")

def main():
    """
    Main entry point for T001a.
    """
    logger = get_logger(__name__)
    logger.info("Starting T001a: Create project directory structure")

    try:
        # 1. Create directories
        create_directories(logger)

        # 2. Verify directories
        if not verify_directories(logger):
            logger.error("Directory verification failed. Aborting log generation.")
            sys.exit(1)

        # 3. Generate setup log
        generate_setup_log(logger)

        logger.info("T001a completed successfully.")
        sys.exit(0)

    except Exception as e:
        logger.exception(f"An error occurred during T001a: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
