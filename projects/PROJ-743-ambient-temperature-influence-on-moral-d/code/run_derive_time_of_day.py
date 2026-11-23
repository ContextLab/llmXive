"""
Runner script for Task T028d: Derive Time-of-Day.
Orchestrates the execution of derive_time_of_day.py.
"""
import sys
import logging
from pathlib import Path

# Add project root to path if necessary, though typically run from root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from setup_logging import setup_logging, get_data_quality_logger
from derive_time_of_day import main as derive_main

def setup_logging_custom():
    """Setup logging for the runner."""
    setup_logging()
    return get_data_quality_logger('derive_time_of_day_runner')

def main():
    logger = setup_logging_custom()
    logger.info("Starting T028d: Derive Time-of-Day runner.")
    
    # Arguments are typically passed via command line or quickstart.md
    # This runner expects them to be passed through sys.argv or we can define defaults
    # For now, we delegate directly to the main logic which parses args
    try:
        derive_main()
        logger.info("T028d: Derive Time-of-Day completed successfully.")
    except Exception as e:
        logger.error(f"T028d: Derive Time-of-Day failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()