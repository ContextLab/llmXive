"""
Verification script for extraction output CSV structure.

This script validates that the extraction output CSV matches the required schema
and contains the minimum number of rows as per FR-001.
"""
import csv
import sys
import logging
from pathlib import Path
from typing import List, Set

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging import get_logger

# Required columns as per task description
REQUIRED_COLUMNS: Set[str] = {
    'snippet_id',
    'repo_url',
    'file_path',
    'median_commit_age',
    'snippet_content',
    'token_count',
    'complexity',
    'token_length'
}

# Minimum row count per FR-001
MIN_ROWS: int = 800

logger = get_logger(__name__)

def verify_csv_structure(csv_path: Path) -> bool:
    """
    Verify that the CSV file exists and has the correct structure.
    
    Args:
        csv_path: Path to the extraction output CSV file
        
    Returns:
        True if verification passes, False otherwise
    """
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return False
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check headers
            if reader.fieldnames is None:
                logger.error("CSV file is empty or has no headers")
                return False
            
            actual_columns = set(reader.fieldnames)
            missing_columns = REQUIRED_COLUMNS - actual_columns
            extra_columns = actual_columns - REQUIRED_COLUMNS
            
            if missing_columns:
                logger.error(f"Missing required columns: {missing_columns}")
                return False
            
            if extra_columns:
                logger.warning(f"Extra columns found (allowed): {extra_columns}")
            
            # Count rows and validate content
            row_count = 0
            valid_rows = 0
            
            for row in reader:
                row_count += 1
                
                # Check for required non-null fields
                if (row.get('snippet_id') and 
                    row.get('repo_url') and 
                    row.get('file_path') and
                    row.get('median_commit_age') is not None and
                    row.get('snippet_content')):
                    valid_rows += 1
                
                # Early exit if we have enough valid rows
                if valid_rows >= MIN_ROWS:
                    break
            
            logger.info(f"Total rows scanned: {row_count}")
            logger.info(f"Valid rows (non-null key fields): {valid_rows}")
            
            if valid_rows < MIN_ROWS:
                logger.error(f"Insufficient valid rows. Found: {valid_rows}, Required: {MIN_ROWS}")
                return False
            
            logger.info("CSV structure verification PASSED")
            return True
            
    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        return False

def main():
    """Main entry point for the verification script."""
    # Default path relative to project root
    extraction_csv = Path("data/extracted/snippets.csv")
    
    # Allow override via command line argument
    if len(sys.argv) > 1:
        extraction_csv = Path(sys.argv[1])
    
    logger.info(f"Verifying extraction output: {extraction_csv}")
    
    success = verify_csv_structure(extraction_csv)
    
    if not success:
        logger.error("Verification FAILED")
        sys.exit(1)
    else:
        logger.info("Verification PASSED")
        sys.exit(0)

if __name__ == "__main__":
    main()
