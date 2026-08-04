"""
Runner script for T015c: Validate OSM noise proxies against Global Soundscapes.

Executes the validation logic and writes validation_log.csv to data/interim/.

FR-002 Compliance: Logs justification for OSM-only data when Global Soundscapes
is unavailable.
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.validation import main as run_validation
from src.utils.logging import setup_logger


def main():
    """Main entry point for T015c validation runner."""
    logger = setup_logger('t015c_validation')
    logger.info("Starting T015c: OSM Noise Proxy Validation")
    
    try:
        exit_code = run_validation()
        
        if exit_code == 0:
            logger.info("T015c validation completed successfully")
        else:
            logger.warning("T015c validation completed with warnings")
        
        return exit_code
        
    except Exception as e:
        logger.error(f"T015c validation failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
