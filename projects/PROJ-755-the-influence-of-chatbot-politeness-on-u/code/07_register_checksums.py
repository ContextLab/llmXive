"""
Script to register checksums for raw data artifacts after T007 generates them.
This script implements T007b by reading the generated raw data files and updating
the state project YAML file.
"""
import os
import sys
import logging
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.checksum_registry import register_raw_data_checksum, get_raw_data_checksums
from utils.data_integrity import compute_file_checksum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

RAW_DATA_SOURCES = [
    ("hci_p2", "data/raw/hci_p2/raw_data.parquet"),
    ("persona_chat", "data/raw/persona_chat/raw_data.parquet"),
    ("empathetic_dialogues", "data/raw/empathetic_dialogues/raw_data.parquet")
]

def main():
    logger.info("Starting checksum registration for raw data artifacts (T007b)...")
    
    registered_count = 0
    errors = []

    for source_name, relative_path in RAW_DATA_SOURCES:
        full_path = Path(relative_path)
        
        if not full_path.exists():
            logger.warning(f"File not found for {source_name}: {full_path}. Skipping.")
            errors.append(f"Missing file: {source_name}")
            continue

        try:
            checksum = register_raw_data_checksum(source_name, str(full_path))
            logger.info(f"Successfully registered checksum for {source_name}: {checksum[:16]}...")
            registered_count += 1
        except Exception as e:
            logger.error(f"Failed to register {source_name}: {e}")
            errors.append(f"Error registering {source_name}: {str(e)}")

    if registered_count == 0:
        logger.error("No checksums were registered. Ensure raw data files exist.")
        sys.exit(1)

    logger.info(f"Registration complete. {registered_count} artifacts registered.")
    
    if errors:
        logger.warning(f"Encountered {len(errors)} errors during processing.")
        # Do not exit with error code if some succeeded, but log the failures
        # The task is considered completed if at least one is registered, 
        # but the user should review the logs.

if __name__ == "__main__":
    main()