"""
Entry point script to execute the checksumming process on the initial data/ structure.
This script fulfills task T001d by verifying integrity and storing checksums.
"""
import sys
import logging
from pathlib import Path

# Ensure the code directory is in the path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data_generation.utils import compute_and_store_checksums

def main():
    """
    Executes the checksumming script on the initial data/ structure.
    Verifies integrity and updates the central state file.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    logger.info("Starting checksum verification for T001d...")
    
    try:
        # Execute the checksum computation and storage
        # This function is expected to walk the data/ directory,
        # compute SHA-256 hashes, and write them to the state file.
        success = compute_and_store_checksums()
        
        if success:
            logger.info("Checksumming completed successfully. Integrity verified.")
            return 0
        else:
            logger.error("Checksumming failed. Integrity check not passed.")
            return 1
    except Exception as e:
        logger.error(f"Unexpected error during checksumming: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
