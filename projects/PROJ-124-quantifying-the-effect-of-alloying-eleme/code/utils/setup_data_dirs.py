"""
Module to create and verify the project's data directory structure.
Implements Task T004a: Create data/raw/ and data/processed/ directories.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple

# Add the parent directory to sys.path to allow imports from 'code'
# This is necessary when running this script directly or via a runner
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CODE_DIR = ROOT_DIR / "code"
DATA_DIR = ROOT_DIR / "data"
STATE_DIR = ROOT_DIR / "state"
OUTPUT_DIR = ROOT_DIR / "output"
TESTS_DIR = ROOT_DIR / "tests"
DOCS_DIR = ROOT_DIR / "docs"
LOGS_DIR = ROOT_DIR / "logs"

def create_data_directories() -> Tuple[List[str], List[str]]:
    """
    Creates the required directory structure for the project.
    
    Specifically addresses Task T004a by ensuring data/raw/ and data/processed/ exist.
    Also ensures other foundational directories exist for the pipeline to run.
    
    Returns:
        Tuple[List[str], List[str]]: (created_paths, failed_paths)
    """
    directories_to_create = [
        DATA_DIR / "raw",
        DATA_DIR / "processed",
        DATA_DIR / "config",
        STATE_DIR,
        OUTPUT_DIR,
        LOGS_DIR,
        # Ensure base data dir exists first
        DATA_DIR,
        # Ensure state and output base dirs exist
        STATE_DIR,
        OUTPUT_DIR,
    ]
    
    created = []
    failed = []
    
    for dir_path in directories_to_create:
        try:
            # exist_ok=True ensures we don't error if it already exists
            dir_path.mkdir(parents=True, exist_ok=True)
            
            # Verify writability by attempting to create a temp file
            test_file = dir_path / ".write_test"
            test_file.touch()
            test_file.unlink()
            
            created.append(str(dir_path))
            logging.info(f"Verified directory: {dir_path}")
        except OSError as e:
            logging.error(f"Failed to create or verify {dir_path}: {e}")
            failed.append(str(dir_path))
        except Exception as e:
            logging.error(f"Unexpected error verifying {dir_path}: {e}")
            failed.append(str(dir_path))
    
    return created, failed

def main():
    """
    Entry point for the script.
    Creates directories and prints verification results.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("setup_data_dirs")
    
    logger.info("Starting directory structure creation (Task T004a)...")
    
    created, failed = create_data_directories()
    
    if created:
        logger.info(f"Successfully created/verified {len(created)} directories:")
        for d in created:
            logger.info(f"  - {d}")
    
    if failed:
        logger.error(f"Failed to create/verify {len(failed)} directories:")
        for d in failed:
            logger.error(f"  - {d}")
        sys.exit(1)
    else:
        logger.info("All required directories are ready.")
        sys.exit(0)

if __name__ == "__main__":
    main()