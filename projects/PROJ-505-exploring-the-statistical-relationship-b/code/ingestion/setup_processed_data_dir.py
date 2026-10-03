"""
Task T009: Create directory `projects/PROJ-505-exploring-the-statistical-relationship-b/data/processed`.

This script ensures the 'processed' data directory exists within the project structure.
It uses the shared directory creation utility.
"""
import sys
from pathlib import Path
import logging

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from utils.mkdirs import ensure_dirs
from utils.logging import get_logger, setup_logging

def main():
    setup_logging()
    logger = get_logger(__name__)
    
    # Define the target directory relative to the project root
    processed_dir = project_root / "data" / "processed"
    
    logger.info(f"Ensuring existence of processed data directory: {processed_dir}")
    ensure_dirs([str(processed_dir)])
    
    if processed_dir.exists():
        logger.info(f"SUCCESS: Directory '{processed_dir}' is ready.")
    else:
        logger.error(f"FAILURE: Directory '{processed_dir}' was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()
