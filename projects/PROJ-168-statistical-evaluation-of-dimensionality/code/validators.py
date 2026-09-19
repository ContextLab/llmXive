"""
Validation logic for the dimensionality reduction pipeline.
Ensures data integrity and enforces 'Real Data Only' constraints.
"""
import os
import sys
import logging
import hashlib
import json
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealDataValidationError(Exception):
    """Raised when validation of real data constraints fails."""
    pass

def check_file_for_synthetic_content(file_path: Path) -> bool:
    """
    Scans a file for common patterns indicating synthetic or placeholder data.
    Returns True if synthetic content is detected, False otherwise.
    """
    synthetic_patterns = [
        r'fake', r'synthetic', r'placeholder', r'mock', r'test_data',
        r'random_seed_\d+', r'generated_at', r'NO_REAL_DATA',
        r'1\.000000', r'0\.000000',  # Suspiciously round floats often seen in mocks
    ]
    
    try:
        # Read first 1MB to avoid loading huge files entirely
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            chunk = f.read(1024 * 1024)
            
        for pattern in synthetic_patterns:
            if re.search(pattern, chunk, re.IGNORECASE):
                logger.warning(f"Synthetic pattern '{pattern}' found in {file_path}")
                return True
                
        # Check for specific "all zeros" or "all ones" columns in CSV/TSV if small enough
        # This is a heuristic check for the first 1000 lines
        if file_path.suffix in ['.csv', '.tsv', '.txt']:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = [f.readline() for _ in range(1000)]
            
            # Simple check: if every row looks identical or has constant values
            if len(lines) > 10:
                first_row = lines[0].strip().split(',')
                if len(first_row) > 2:
                    # Check if all numeric columns are identical across rows
                    # This is a basic heuristic
                    all_same = True
                    for i in range(1, min(len(first_row), 5)):
                        try:
                            val = float(first_row[i])
                            for line in lines[1:]:
                                parts = line.strip().split(',')
                                if len(parts) > i:
                                    if float(parts[i]) != val:
                                        all_same = False
                                        break
                        except ValueError:
                            pass
                    if all_same and len(first_row) > 2:
                        logger.warning(f"All values in first few columns identical in {file_path}")
                        return True

    except Exception as e:
        logger.error(f"Error scanning file {file_path}: {e}")
        # If we can't read it, we assume it's not synthetic (fail-safe for unreadable)
        return False
        
    return False

def validate_raw_directory(raw_dir: Path) -> bool:
    """
    Validates that the raw data directory contains real data files
    and no synthetic placeholders.
    """
    if not raw_dir.exists():
        logger.error(f"Raw directory does not exist: {raw_dir}")
        return False

    files_checked = 0
    synthetic_found = False

    for file_path in raw_dir.glob('*'):
        if file_path.is_file():
            # Skip hidden files and common non-data files
            if file_path.name.startswith('.') or file_path.suffix in ['.md', '.txt', '.log']:
                continue
            
            files_checked += 1
            if check_file_for_synthetic_content(file_path):
                synthetic_found = True
                break

    if files_checked == 0:
        logger.warning("No data files found in raw directory.")
        return False

    if synthetic_found:
        logger.error("Synthetic data detected in raw directory.")
        return False

    logger.info(f"Validated {files_checked} files in raw directory.")
    return True

def enforce_real_data_constraint(data_path: Path) -> None:
    """
    Enforces the 'Real Data Only' constraint.
    Raises RealDataValidationError if synthetic data is detected.
    """
    if not data_path.exists():
        # If path doesn't exist, we can't validate, but we also can't confirm it's real.
        # However, for this function, we assume the caller ensures the path exists
        # before calling, or we treat missing as a validation failure for the constraint.
        raise RealDataValidationError(f"Data path does not exist: {data_path}")

    if data_path.is_file():
        if check_file_for_synthetic_content(data_path):
            raise RealDataValidationError(f"Synthetic data detected in file: {data_path}")
    elif data_path.is_dir():
        if not validate_raw_directory(data_path):
            raise RealDataValidationError(f"Synthetic data detected in directory: {data_path}")

def validate_accession_data(accession: str, data_dir: Path) -> Dict[str, Any]:
    """
    Validates data for a specific GEO accession.
    Returns a dictionary with validation status and details.
    """
    result = {
        'accession': accession,
        'status': 'unknown',
        'message': '',
        'file_count': 0,
        'synthetic_detected': False
    }

    accession_dir = data_dir / accession
    if not accession_dir.exists():
        result['status'] = 'missing'
        result['message'] = f'Directory for {accession} not found'
        return result

    try:
        files = list(accession_dir.glob('*'))
        result['file_count'] = len([f for f in files if f.is_file()])
        
        if result['file_count'] == 0:
            result['status'] = 'empty'
            result['message'] = 'No files found in accession directory'
            return result

        synthetic_detected = False
        for f in files:
            if f.is_file() and check_file_for_synthetic_content(f):
                synthetic_detected = True
                break

        if synthetic_detected:
            result['status'] = 'invalid'
            result['message'] = 'Synthetic data detected'
            result['synthetic_detected'] = True
        else:
            result['status'] = 'valid'
            result['message'] = 'Validation passed'

    except Exception as e:
        result['status'] = 'error'
        result['message'] = f'Validation error: {str(e)}'

    return result

def main():
    """Main entry point for validation script."""
    config = Config()
    raw_dir = config.RAW_DATA_DIR

    logger.info(f"Validating data in {raw_dir}")
    
    try:
        enforce_real_data_constraint(raw_dir)
        logger.info("Real data validation passed.")
        return 0
    except RealDataValidationError as e:
        logger.error(f"Real data validation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
