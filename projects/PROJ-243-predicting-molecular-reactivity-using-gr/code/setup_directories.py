import os
import sys
import logging
from config import ensure_directories

def setup_script_logging():
    """Configure logging for the directory setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def main():
    """Create all required project directories."""
    logger = setup_script_logging()
    logger.info("Starting directory setup...")
    
    # ensure_directories is imported from config and handles the actual creation
    ensure_directories()
    
    logger.info("Directory setup completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())