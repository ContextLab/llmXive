"""
Validate raw AGP data for required fields: Age, Sex, BMI, Diet.
Logs errors if missing.
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import project utilities
from config import get_project_root
from logging_config import get_preprocess_logger, log_structured_event

# Required fields for AGP data
REQUIRED_FIELDS = ['Age', 'Sex', 'BMI', 'Diet']

def get_logger():
    """Get the preprocessor logger."""
    return get_preprocess_logger()

def load_raw_data(file_path: str) -> Optional[List[Dict[str, Any]]]:
    """
    Load raw microbiome data from a CSV file.
    
    Args:
        file_path: Path to the raw data file.
        
    Returns:
        List of dictionaries representing rows, or None if file not found.
    """
    logger = get_logger()
    
    if not os.path.exists(file_path):
        logger.error(f"Raw data file not found: {file_path}")
        return None
    
    try:
        # Try to load as CSV (common for AGP data)
        import pandas as pd
        df = pd.read_csv(file_path)
        return df.to_dict('records')
    except Exception as e:
        logger.error(f"Failed to load raw data from {file_path}: {e}")
        return None

def validate_fields(data: List[Dict[str, Any]], required_fields: List[str]) -> Dict[str, Any]:
    """
    Check raw data for required fields and missing values.
    
    Args:
        data: List of row dictionaries.
        required_fields: List of required field names.
        
    Returns:
        Dictionary with validation results.
    """
    logger = get_logger()
    results = {
        'total_rows': len(data),
        'valid_rows': 0,
        'invalid_rows': 0,
        'missing_fields': {},
        'errors': []
    }
    
    # Initialize missing field counters
    for field in required_fields:
        results['missing_fields'][field] = 0
    
    for i, row in enumerate(data):
        row_valid = True
        row_errors = []
        
        for field in required_fields:
            # Check if field exists and is not None/empty
            if field not in row or row[field] is None or (isinstance(row[field], str) and row[field].strip() == ''):
                results['missing_fields'][field] += 1
                row_valid = False
                row_errors.append(f"Missing or empty field: {field}")
        
        if row_valid:
            results['valid_rows'] += 1
        else:
            results['invalid_rows'] += 1
            results['errors'].append({
                'row_index': i,
                'errors': row_errors
            })
            
            # Log first 5 errors to avoid flooding
            if i < 5:
                logger.warning(f"Row {i} validation failed: {row_errors}")
    
    # Log summary
    log_structured_event(
        event_type='validation_summary',
        data={
            'file': file_path,
            'total_rows': results['total_rows'],
            'valid_rows': results['valid_rows'],
            'invalid_rows': results['invalid_rows'],
            'missing_field_counts': results['missing_fields']
        }
    )
    
    return results

def main():
    """Main entry point for validation."""
    parser = argparse.ArgumentParser(description='Validate raw AGP microbiome data fields')
    parser.add_argument('--input', '-i', type=str, required=True, 
                      help='Path to raw AGP data file (CSV)')
    parser.add_argument('--output', '-o', type=str, default=None,
                      help='Path to output validation report (JSON). If None, only logs.')
    
    args = parser.parse_args()
    
    logger = get_logger()
    logger.info(f"Starting validation of raw AGP data: {args.input}")
    
    # Load data
    data = load_raw_data(args.input)
    if data is None:
        logger.error("Failed to load data. Validation aborted.")
        sys.exit(1)
    
    # Validate fields
    results = validate_fields(data, REQUIRED_FIELDS)
    
    # Determine exit code
    exit_code = 0
    if results['invalid_rows'] > 0:
        logger.warning(f"Validation found {results['invalid_rows']} rows with missing required fields.")
        # Check if critical threshold is exceeded (e.,g., > 20% invalid)
        invalid_rate = results['invalid_rows'] / results['total_rows']
        if invalid_rate > 0.2:
            logger.error(f"Invalid row rate ({invalid_rate:.2%}) exceeds 20% threshold.")
            exit_code = 1
    else:
        logger.info("All rows passed validation.")
    
    # Save report if requested
    if args.output:
        output_path = Path(get_project_root()) / args.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Validation report saved to: {output_path}")
    
    logger.info("Validation completed.")
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
