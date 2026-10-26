"""
Setup the required directory layout for the project.
This script implements Task T001 by ensuring all necessary
source, test, data, and specification directories exist.
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# The canonical list of directories required by T001
_REQUIRED_DIRS = [
    "code/src/config",
    "code/src/extraction",
    "code/src/detection",
    "code/src/inference",
    "code/src/analysis",
    "code/src/reporting",
    "code/src/pipeline",
    "code/src/cli",
    "code/tests/unit",
    "code/tests/integration",
    "code/tests/contract",
    "code/data/raw",
    "code/data/annotations",
    "code/data/derived",
    "code/data/results",
    "code/logs",
    "specs/001-evaluating-the-impact-of-code-generation/contracts",
]

def create_directories(extra_paths: Optional[List[Path]] = None) -> List[Path]:
    """
    Ensure that all required directories (and any extra_paths) exist.
    Returns a list of absolute paths to the created/verified directories.
    """
    created = []
    
    # Combine required paths with any optional extras
    all_paths = [_REQUIRED_DIRS] # This is a list of strings
    # Correction: _REQUIRED_DIRS is already the list.
    
    for path_str in _REQUIRED_DIRS:
        p = Path(path_str).resolve()
        p.mkdir(parents=True, exist_ok=True)
        created.append(p)
    
    if extra_paths:
        for p in extra_paths:
            abs_p = p.resolve()
            abs_p.mkdir(parents=True, exist_ok=True)
            created.append(abs_p)
            
    return created

def main() -> int:
    """
    CLI entry point: create the required layout and exit with status 0 on success.
    """
    try:
        logger.info("Initializing project directory structure...")
        created_paths = create_directories()
        
        # Verification check
        for p in created_paths:
            if not p.is_dir():
                logger.error(f"Failed to verify directory: {p}")
                return 1
        
        logger.info(f"Successfully verified {len(created_paths)} directories.")
        return 0
    except Exception as e:
        logger.exception(f"Unexpected error during directory setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())