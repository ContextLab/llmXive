import sys
import logging
from pathlib import Path

# Add project root to path to ensure imports work regardless of cwd
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from setup_logging import setup_logging, get_data_quality_logger
from update_state_checksum_era5_full import main

def main_entry():
    """Entry point for the T002e checksum update script."""
    logger = setup_logging()
    logger.info("Starting T002e: Checksum Full ERA5 File update.")
    
    try:
        main()
        logger.info("T002e completed successfully.")
    except Exception as e:
        logger.error(f"T002e failed with error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main_entry()
