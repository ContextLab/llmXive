"""
Task T005c: Verify data/derived/valid_subjects.csv exists and contains only subjects not in exclusions.log.

This script performs the verification logic required by T005c:
1. Checks existence of data/derived/valid_subjects.csv
2. Checks existence of data/raw/exclusions.log
3. Loads both files
4. Verifies that no subject in valid_subjects.csv appears in exclusions.log
5. Reports the count of valid subjects and exclusions
6. Exits with code 0 on success, 1 on failure
"""

import os
import csv
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_excluded_subjects(exclusions_path: Path) -> set:
    """Load subject IDs from the exclusions log file."""
    excluded = set()
    if not exclusions_path.exists():
        raise FileNotFoundError(f"Exclusions log not found at {exclusions_path}")
    
    with open(exclusions_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'subject_id' in row:
                excluded.add(row['subject_id'])
    
    logger.info(f"Loaded {len(excluded)} excluded subjects from {exclusions_path}")
    return excluded

def load_valid_subjects(valid_path: Path) -> set:
    """Load subject IDs from the valid subjects CSV file."""
    valid = set()
    if not valid_path.exists():
        raise FileNotFoundError(f"Valid subjects file not found at {valid_path}")
    
    with open(valid_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'subject_id' in row:
                valid.add(row['subject_id'])
    
    logger.info(f"Loaded {len(valid)} valid subjects from {valid_path}")
    return valid

def verify_no_overlap(valid_subjects: set, excluded_subjects: set) -> bool:
    """Verify that no subject appears in both valid and excluded lists."""
    overlap = valid_subjects & excluded_subjects
    if overlap:
        logger.error(f"CRITICAL: Found {len(overlap)} subjects in both valid and excluded lists:")
        for subj in sorted(overlap)[:10]:
            logger.error(f"  - {subj}")
        if len(overlap) > 10:
            logger.error(f"  ... and {len(overlap) - 10} more")
        return False
    return True

def main():
    """Main verification routine for T005c."""
    # Define paths relative to project root
    project_root = Path(__file__).parent.parent
    valid_subjects_path = project_root / "data" / "derived" / "valid_subjects.csv"
    exclusions_path = project_root / "data" / "raw" / "exclusions.log"

    logger.info("Starting T005c verification...")
    logger.info(f"Valid subjects path: {valid_subjects_path}")
    logger.info(f"Exclusions path: {exclusions_path}")

    try:
        # Check file existence
        if not valid_subjects_path.exists():
            logger.error(f"FAILED: {valid_subjects_path} does not exist")
            sys.exit(1)
        
        if not exclusions_path.exists():
            logger.error(f"FAILED: {exclusions_path} does not exist")
            sys.exit(1)

        # Load data
        valid_subjects = load_valid_subjects(valid_subjects_path)
        excluded_subjects = load_excluded_subjects(exclusions_path)

        # Verify no overlap
        if not verify_no_overlap(valid_subjects, excluded_subjects):
            logger.error("FAILED: Valid subjects list contains excluded subjects")
            sys.exit(1)

        # Success
        logger.info("SUCCESS: Verification passed")
        logger.info(f"  - Valid subjects count: {len(valid_subjects)}")
        logger.info(f"  - Excluded subjects count: {len(excluded_subjects)}")
        logger.info(f"  - No overlap detected between valid and excluded lists")
        sys.exit(0)

    except Exception as e:
        logger.error(f"FAILED with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
