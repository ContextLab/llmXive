import sys
import json
from pathlib import Path
from utils.config_manager import initialize_project_config, initialize_checksums_file, update_checksums, verify_checksums
from utils.logging_config import get_logger

logger = get_logger(__name__)

def main():
    """
    Entry point to initialize and verify the project checksums structure.
    This script ensures data/.checksums.json exists and is valid.
    """
    logger.info("Initializing checksums system...")
    config = initialize_project_config()
    
    # Ensure the file exists with the correct structure
    initialize_checksums_file(config)
    
    logger.info(f"Checksums file structure verified at: {config.checksums_path}")
    
    # Example: Verify against a dummy list (empty for now)
    # In a real pipeline, this would be called with specific artifact paths
    if verify_checksums(config, []):
        logger.info("Checksum system initialized and verified.")
        return 0
    else:
        logger.error("Checksum system verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())