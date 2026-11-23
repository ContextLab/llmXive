#!/usr/bin/env python3
"""
Gate Launch Script for T037.

This script acts as the final validation gate before the study can proceed to
data collection. It invokes validation functions from `code/data_validation.py`
to ensure:
1. FR-008: Metadata matching (pose, lighting) between AI and Human sets.
2. FR-009: Visual indistinguishability (p > 0.05) based on pre-test results.

If any validation fails, the script raises SystemExit(1) with a descriptive
error message, preventing the study launch.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.data_validation import (
    check_metadata_matching,
    check_visual_indistinguishability,
    DataValidationError
)
from code.logging_config import setup_logger

# Configure logging
logger = setup_logger("gate_launch", level=logging.INFO)

def main():
    logger.info("=" * 60)
    logger.info("Starting Gate Launch Validation (T037)")
    logger.info("=" * 60)

    try:
        # 1. Check FR-008: Metadata Matching
        logger.info("Checking FR-008: Metadata matching between AI and Human sets...")
        try:
            is_matched = check_metadata_matching()
            if not is_matched:
                raise DataValidationError(
                    "FR-008 Failed: Metadata matching check failed. "
                    "AI and Human stimulus sets do not have matching metadata (pose, lighting)."
                )
            logger.info("FR-008 PASSED: Metadata matching verified.")
        except DataValidationError as e:
            logger.error(f"FR-008 FAILED: {e}")
            raise

        # 2. Check FR-009: Visual Indistinguishability
        logger.info("Checking FR-009: Visual indistinguishability (pre-test results)...")
        try:
            is_indistinguishable = check_visual_indistinguishability()
            if not is_indistinguishable:
                raise DataValidationError(
                    "FR-009 Failed: Visual indistinguishability check failed. "
                    "Pre-test p-value <= 0.05 indicates AI and Human images are distinguishable."
                )
            logger.info("FR-009 PASSED: Visual indistinguishability verified.")
        except DataValidationError as e:
            logger.error(f"FR-009 FAILED: {e}")
            raise

        logger.info("=" * 60)
        logger.info("ALL VALIDATION GATES PASSED. Study launch permitted.")
        logger.info("=" * 60)
        sys.exit(0)

    except DataValidationError as e:
        logger.error("=" * 60)
        logger.error("VALIDATION GATE FAILED. Study launch BLOCKED.")
        logger.error(f"Reason: {e}")
        logger.error("=" * 60)
        sys.exit(1)
    except Exception as e:
        logger.error("=" * 60)
        logger.error("UNEXPECTED ERROR during gate validation.")
        logger.error(f"Error: {e}")
        logger.error("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()