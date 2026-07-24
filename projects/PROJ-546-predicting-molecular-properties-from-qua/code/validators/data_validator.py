"""
Data validator for the molecular properties dataset.

Verifies that the downloaded CSV contains required columns (SMILES, experimental_barrier)
and that data types are correct (SMILES is string, experimental_barrier is float).
Implements FR-001 requirements.
"""
import csv
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ['SMILES', 'experimental_barrier']

class ValidationError(Exception):
    """Raised when data validation fails."""
    pass

def validate_columns(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify that the CSV file contains all required columns.
    
    Args:
        file_path: Path to the CSV file to validate
        
    Returns:
        Tuple of (success: bool, errors: List[str])
    """
    errors = []
    
    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            if header is None:
                errors.append("CSV file is empty (no header row)")
                return False, errors
            
            # Normalize header names (strip whitespace)
            header = [col.strip() for col in header]
            
            missing_cols = []
            for col in REQUIRED_COLUMNS:
                if col not in header:
                    missing_cols.append(col)
            
            if missing_cols:
                errors.append(f"Required columns not found. Expected: {REQUIRED_COLUMNS}, Found: {header}")
                return False, errors
            
            logger.info(f"Column validation passed. Found columns: {header}")
            return True, []
            
    except csv.Error as e:
        errors.append(f"CSV parsing error: {str(e)}")
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected error during column validation: {str(e)}")
        return False, errors

def validate_data_types(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify that data types in the CSV are correct.
    
    - SMILES: non-empty string
    - experimental_barrier: valid float (can be negative for barriers)
    
    Args:
        file_path: Path to the CSV file to validate
        
    Returns:
        Tuple of (success: bool, errors: List[str])
    """
    errors = []
    row_count = 0
    error_rows = []
    
    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Verify columns exist first
            if reader.fieldnames is None:
                errors.append("CSV file is empty")
                return False, errors
            
            fieldnames = [col.strip() for col in reader.fieldnames]
            
            for col in REQUIRED_COLUMNS:
                if col not in fieldnames:
                    errors.append(f"Required column '{col}' not found in CSV")
                    return False, errors
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                row_count += 1
                row_errors = []
                
                # Validate SMILES
                smiles = row.get('SMILES', '').strip()
                if not smiles:
                    row_errors.append(f"Row {row_num}: SMILES is empty or missing")
                
                # Validate experimental_barrier
                barrier_str = row.get('experimental_barrier', '').strip()
                if not barrier_str:
                    row_errors.append(f"Row {row_num}: experimental_barrier is empty or missing")
                else:
                    try:
                        barrier_val = float(barrier_str)
                        # Barriers can be negative in some contexts, but typically positive
                        # We accept any valid float here
                        if not isinstance(barrier_val, (int, float)):
                            row_errors.append(f"Row {row_num}: experimental_barrier is not a valid number")
                    except ValueError:
                        row_errors.append(f"Row {row_num}: experimental_barrier '{barrier_str}' is not a valid float")
                
                if row_errors:
                    error_rows.extend(row_errors)
                    if len(error_rows) > 10:  # Limit error reporting
                        break
            
            if error_rows:
                errors.extend(error_rows[:10])  # Report first 10 errors
                if len(error_rows) > 10:
                    errors.append(f"... and {len(error_rows) - 10} more errors")
                return False, errors
            
            logger.info(f"Data type validation passed for {row_count} rows")
            return True, []
            
    except csv.Error as e:
        errors.append(f"CSV parsing error: {str(e)}")
        return False, errors
    except Exception as e:
        errors.append(f"Unexpected error during data type validation: {str(e)}")
        return False, errors

def validate_physical_ranges(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Verify that data values are within physically reasonable ranges.
    
    Args:
        file_path: Path to the CSV file to validate
        
    Returns:
        Tuple of (success: bool, errors: List[str])
    """
    errors = []
    row_count = 0
    warning_rows = []
    
    if not file_path.exists():
        errors.append(f"File not found: {file_path}")
        return False, errors
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                row_count += 1
                
                barrier_str = row.get('experimental_barrier', '').strip()
                if barrier_str:
                    try:
                        barrier_val = float(barrier_str)
                        # Typical reaction barriers are positive and within reasonable bounds
                        # Very large negative values or extremely large positive values might indicate errors
                        if barrier_val < -100.0:
                            warning_rows.append(f"Row {row_num}: Unusually negative barrier ({barrier_val})")
                        elif barrier_val > 1000.0:
                            warning_rows.append(f"Row {row_num}: Unusually large barrier ({barrier_val})")
                    except ValueError:
                        pass  # Already caught in data type validation
                
                # SMILES should not be empty (checked in data type validation)
            
            if warning_rows:
                logger.warning(f"Found {len(warning_rows)} rows with unusual values")
                # We don't fail on warnings, just log them
                return True, []
            
            logger.info(f"Physical range validation passed for {row_count} rows")
            return True, []
            
    except Exception as e:
        errors.append(f"Unexpected error during physical range validation: {str(e)}")
        return False, errors

def validate_full(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Run all validations on the CSV file.
    
    Args:
        file_path: Path to the CSV file to validate
        
    Returns:
        Tuple of (success: bool, errors: List[str])
    """
    all_errors = []
    
    logger.info(f"Starting full validation for: {file_path}")
    
    # Validate columns
    success, errors = validate_columns(file_path)
    if not success:
        all_errors.extend(errors)
        logger.error(f"Column validation failed: {errors}")
        return False, all_errors
    
    # Validate data types
    success, errors = validate_data_types(file_path)
    if not success:
        all_errors.extend(errors)
        logger.error(f"Data type validation failed: {errors}")
        return False, all_errors
    
    # Validate physical ranges (warnings only, don't fail)
    success, errors = validate_physical_ranges(file_path)
    if not success:
        all_errors.extend(errors)
        logger.warning(f"Physical range validation issues: {errors}")
    
    logger.info("Full validation completed successfully")
    return True, []

def main():
    """Main entry point for the data validator."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate downloaded molecular properties CSV file'
    )
    parser.add_argument(
        'file_path',
        type=Path,
        help='Path to the CSV file to validate'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success, errors = validate_full(args.file_path)
    
    if success:
        logger.info(f"Validation PASSED for {args.file_path}")
        sys.exit(0)
    else:
        logger.error(f"Validation FAILED for {args.file_path}")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)

if __name__ == '__main__':
    main()