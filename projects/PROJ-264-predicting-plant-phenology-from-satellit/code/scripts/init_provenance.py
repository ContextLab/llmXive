"""
Script to initialize the provenance tracking system.

This script creates the initial data/provenance.yaml file
with the standard schema and metadata.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.provenance import initialize_provenance_file, PROVENANCE_FILE_PATH
from src.lib.utils import setup_logging

logger = setup_logging(__name__)


def main() -> int:
    """
    Main entry point for initializing provenance.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("Initializing provenance file...")
        initialize_provenance_file()
        
        if PROVENANCE_FILE_PATH.exists():
            logger.info(f"Successfully initialized provenance at {PROVENANCE_FILE_PATH}")
            return 0
        else:
            logger.error("Failed to create provenance file")
            return 1
            
    except Exception as e:
        logger.error(f"Error initializing provenance: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
