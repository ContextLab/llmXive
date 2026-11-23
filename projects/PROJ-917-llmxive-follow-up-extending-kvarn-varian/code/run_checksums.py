"""
Script to execute checksumming on the data directory and update the central state file.
This satisfies task T001d: Execute checksumming script on initial data/ structure to verify integrity.
"""
import sys
import logging
from pathlib import Path

# Adjust import to match the provided API surface
# The API surface lists: from run_checksums import main
# And imports from data_generation.utils import compute_and_store_checksums
from data_generation.utils import compute_and_store_checksums

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Entry point for the checksum execution script.
    Computes checksums for all files in data/ and updates the state file.
    """
    logger.info("Starting checksum verification for data directory...")
    
    # The path to the data directory relative to project root
    data_dir = Path("data")
    
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir.absolute()}")
        sys.exit(1)
    
    try:
        # compute_and_store_checksums is expected to handle the logic of:
        # 1. Scanning data_dir
        # 2. Computing SHA-256
        # 3. Updating state/projects/PROJ-917-llmxive-follow-up-extending-kvarn-varian.yaml
        result = compute_and_store_checksums(data_dir)
        
        if result:
            logger.info("Checksumming completed successfully.")
            logger.info(f"Updated artifact hashes in state file.")
            sys.exit(0)
        else:
            logger.error("Checksumming process returned failure.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error during checksum execution: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
