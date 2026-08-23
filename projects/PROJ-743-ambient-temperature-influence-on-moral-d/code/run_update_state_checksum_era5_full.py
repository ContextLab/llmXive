"""
Runner script for T002d: Checksum ERA5 Full Dataset.

This script provides a clean entry point to execute the checksum computation
and state file update for the full ERA5 dataset.
"""
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point."""
    logger.info("Starting T002d: Checksum ERA5 Full Dataset")
    
    try:
        # Import and run the main logic
        from update_state_checksum_era5_full import main as checksum_main
        exit_code = checksum_main()
        return exit_code
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())