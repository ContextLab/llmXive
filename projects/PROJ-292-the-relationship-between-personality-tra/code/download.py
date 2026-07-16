"""
Data download utility script.

This script handles the initial fetch of real data from external sources.
It is invoked by the quickstart run-book to validate data availability.

Usage:
    python code/download.py --validate
    python code/download.py --force-synthetic  # Only if real data unavailable
"""
import os
import sys
import argparse
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from code.data_ingestion import run_ingestion_pipeline
from code.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def validate_data():
    """
    Attempt to fetch real data and validate its presence.
    Returns 0 if real data is available, 1 if not (and no synthetic fallback).
    """
    logger.info("Validating data availability...")
    
    # Check if FORCE_SYNTHETIC is set
    force_synthetic = os.environ.get('FORCE_SYNTHETIC', '0').lower() == '1'
    
    if force_synthetic:
        logger.warning("FORCE_SYNTHETIC=1 detected. Will attempt synthetic generation if real data fails.")
    
    try:
        data_path = run_ingestion_pipeline()
        
        # Validate the output file exists
        if data_path and Path(data_path).exists():
            logger.info(f"Data validation successful. File: {data_path}")
            return 0
        else:
            logger.error("Data ingestion completed but output file not found.")
            return 1
            
    except SystemExit as e:
        if e.code == 0:
            logger.info("Data validation completed (synthetic fallback used).")
            return 0
        else:
            logger.error("Data validation failed. Real data unavailable and synthetic not forced.")
            return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description='Data download and validation utility for Personality-AI Feedback study.'
    )
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate that real data is available or synthetic fallback is configured.'
    )
    parser.add_argument(
        '--force-synthetic',
        action='store_true',
        help='Force synthetic data generation if real data is unavailable.'
    )
    
    args = parser.parse_args()
    
    if args.validate:
        return validate_data()
    elif args.force_synthetic:
        os.environ['FORCE_SYNTHETIC'] = '1'
        logger.info("Running with synthetic fallback enabled.")
        return validate_data()
    else:
        parser.print_help()
        return 0

if __name__ == "__main__":
    sys.exit(main())