#!/usr/bin/env python3
"""
Script to execute T092: Update data_manifest.json with generated ground truth dataset.

This script ensures that:
1. The ground truth file exists (dependency T091)
2. The manifest is updated with checksum and generation parameters
3. The manifest is validated after update
"""
import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.update_manifest_ground_truth import main as update_manifest_main
from code.data.manifest_validator import validate_manifest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Execute T092 task."""
    logger.info("=" * 60)
    logger.info("Starting T092: Update data_manifest.json with ground truth dataset")
    logger.info("=" * 60)
    
    try:
        # Step 1: Update manifest with ground truth
        logger.info("Step 1: Updating manifest with ground truth dataset...")
        exit_code = update_manifest_main()
        
        if exit_code != 0:
            logger.error("Failed to update manifest with ground truth")
            return exit_code
        
        logger.info("Manifest updated successfully")
        
        # Step 2: Validate the updated manifest
        logger.info("Step 2: Validating updated manifest...")
        from code.config import DATA_MANIFEST_PATH
        is_valid = validate_manifest(DATA_MANIFEST_PATH)
        
        if not is_valid:
            logger.error("Manifest validation failed")
            return 1
        
        logger.info("Manifest validation passed")
        logger.info("=" * 60)
        logger.info("T092 COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error during T092 execution: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())