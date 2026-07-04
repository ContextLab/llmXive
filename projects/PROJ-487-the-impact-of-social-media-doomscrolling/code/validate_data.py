"""
Data validation module for US1 fetched data.
Validates ISO8601 date formats and float values for fetched datasets.
"""
import csv
import sys
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

from config import Configuration, ConfigError
from logging_config import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


def validate_date_iso8601(date_str: str) -> bool:
    """
    Validates if a string is in ISO8601 date format (YYYY-MM-DD).
    
    Args:
        date_str: String to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not date_str or not isinstance(date_str, str):
        return False
        
    # Strict ISO8601 date format: YYYY-MM-DD
    pattern = r'^\d{4}-\d{2}-\d{2}$'
    if not re.match(pattern, date_str):
        return False
        
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def validate_float_value(value: Any) -> Tuple[bool, Optional[float]]:
    """
    Validates if a value can be converted to a float.
    
    Args:
        value: Value to validate
        
    Returns:
        Tuple of (is_valid, converted_value)
    """
    if value is None:
        return False, None
        
    try:
        float_val = float(value)
        # Check for NaN and Inf
        if float_val != float_val or float_val in (float('inf'), float('-inf')):
            return False, None
        return True, float_val
    except (ValueError, TypeError):
        return False, None


def validate_row(row: Dict[str, Any], expected_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validates a single data row.
    
    Args:
        row: Dictionary representing a data row
        expected_columns: List of column names that must be present
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Check required columns
    for col in expected_columns:
        if col not in row:
            errors.append(f"Missing required column: {col}")
            continue
            
        value = row[col]
        
        # Validate date column
        if col.lower() == 'date':
            if not validate_date_iso8601(str(value)):
                errors.append(f"Invalid date format in '{col}': {value}")
                
        # Validate value columns (numeric)
        elif col.lower() in ['value', 'avgtone', 'search_volume']:
            is_valid, _ = validate_float_value(value)
            if not is_valid:
                errors.append(f"Invalid float value in '{col}': {value}")
                
    return len(errors) == 0, errors


def validate_csv_file(
    file_path: str, 
    expected_columns: List[str],
    min_rows: int = 1
) -> Dict[str, Any]:
    """
    Validates an entire CSV file for date format and float values.
    
    Args:
        file_path: Path to the CSV file
        expected_columns: List of expected column names
        min_rows: Minimum number of data rows required
        
    Returns:
        Dictionary with validation results
    """
    path = Path(file_path)
    if not path.exists():
        raise ValidationError(f"File not found: {file_path}")
        
    results = {
        'valid': True,
        'total_rows': 0,
        'valid_rows': 0,
        'invalid_rows': 0,
        'errors': [],
        'file_path': str(path)
    }
    
    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check headers
            if reader.fieldnames is None:
                results['valid'] = False
                results['errors'].append("CSV file is empty or has no headers")
                return results
                
            missing_cols = set(expected_columns) - set(reader.fieldnames)
            if missing_cols:
                results['valid'] = False
                results['errors'].append(f"Missing columns: {missing_cols}")
                return results
                
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1-indexed, header is row 1)
                results['total_rows'] += 1
                is_valid, row_errors = validate_row(row, expected_columns)
                
                if is_valid:
                    results['valid_rows'] += 1
                else:
                    results['invalid_rows'] += 1
                    results['valid'] = False
                    for err in row_errors:
                        results['errors'].append(f"Row {row_num}: {err}")
                        
    except Exception as e:
        results['valid'] = False
        results['errors'].append(f"Error reading file: {str(e)}")
        return results
        
    # Check minimum rows
    if results['valid_rows'] < min_rows:
        results['valid'] = False
        results['errors'].append(
            f"Insufficient valid data rows: {results['valid_rows']} (minimum: {min_rows})"
        )
        
    return results


def validate_and_save_report(
    file_path: str,
    report_path: str,
    expected_columns: List[str],
    min_rows: int = 1
) -> bool:
    """
    Validates a CSV file and saves a validation report.
    
    Args:
        file_path: Path to the CSV file to validate
        report_path: Path where the report will be saved
        expected_columns: List of expected column names
        min_rows: Minimum number of valid rows required
        
    Returns:
        True if validation passed, False otherwise
    """
    try:
        results = validate_csv_file(file_path, expected_columns, min_rows)
        
        # Create report directory if needed
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("Data Validation Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"File: {results['file_path']}\n")
            f.write(f"Status: {'PASSED' if results['valid'] else 'FAILED'}\n")
            f.write(f"Total Rows: {results['total_rows']}\n")
            f.write(f"Valid Rows: {results['valid_rows']}\n")
            f.write(f"Invalid Rows: {results['invalid_rows']}\n\n")
            
            if results['errors']:
                f.write("Errors:\n")
                for error in results['errors']:
                    f.write(f"  - {error}\n")
            else:
                f.write("No errors found.\n")
                
        if results['valid']:
            logger.info(f"Validation passed for {file_path}: {results['valid_rows']} valid rows")
        else:
            logger.error(f"Validation failed for {file_path}: {len(results['errors'])} errors")
            
        return results['valid']
        
    except Exception as e:
        logger.error(f"Validation process failed: {str(e)}")
        return False


def main():
    """Main entry point for validation script."""
    try:
        config = Configuration()
        
        # Validate GDELT data
        gdelt_path = config.get('gdelt_raw_path', 'data/raw/gdelt_sentiment.csv')
        gdelt_columns = ['date', 'value', 'source']
        gdelt_report = 'output/validation/gdelt_validation_report.txt'
        
        logger.info(f"Validating GDELT data: {gdelt_path}")
        gdelt_valid = validate_and_save_report(
            gdelt_path, 
            gdelt_report, 
            gdelt_columns
        )
        
        # Validate Trends data
        trends_path = config.get('trends_raw_path', 'data/raw/trends_anxiety.csv')
        trends_columns = ['date', 'value', 'source']
        trends_report = 'output/validation/trends_validation_report.txt'
        
        logger.info(f"Validating Trends data: {trends_path}")
        trends_valid = validate_and_save_report(
            trends_path,
            trends_report,
            trends_columns
        )
        
        if gdelt_valid and trends_valid:
            logger.info("All data validation checks passed.")
            sys.exit(0)
        else:
            logger.error("Data validation failed for one or more datasets.")
            sys.exit(1)
            
    except ConfigError as e:
        logger.error(f"Configuration error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()