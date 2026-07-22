"""
Script to initialize the data directory structure and checksum tracking system.
This corresponds to Task T006.
"""
import sys
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.utils.checksum_tracker import initialize_directories, track_directory
from code.utils.logger import setup_logging, get_logger
from code.config import get_path

def main():
    logger = setup_logging()
    logger.info("Starting data directory structure setup (Task T006)...")

    # 1. Initialize directory structure and registry
    initialize_directories()

    # 2. Define paths
    raw_dir = get_path("data", "raw")
    processed_dir = get_path("data", "processed")
    registry_dir = get_path("data", "registry")

    logger.info(f"Ensured existence of: {raw_dir}")
    logger.info(f"Ensured existence of: {processed_dir}")
    logger.info(f"Ensured existence of: {registry_dir}")

    # 3. Verify registry file exists
    registry_file = get_path("data", "registry", "checksums.json")
    if registry_file.exists():
        logger.info(f"Checksum registry initialized at: {registry_file}")
    else:
        logger.error(f"Failed to initialize checksum registry at: {registry_file}")
        return 1

    logger.info("Data directory structure setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
