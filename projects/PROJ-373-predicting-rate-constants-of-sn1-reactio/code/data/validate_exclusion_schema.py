import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports if running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DataConfig
from utils.logger import get_logger
import yaml

def setup_validation_logger(log_path: Path) -> logging.Logger:
    """Setup logging for the validation script."""
    logger = get_logger("exclusion_validation", log_path)
    return logger

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the exclusion report schema from YAML."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_row(row: Dict[str, str], schema: Dict[str, Any]) -> Optional[str]:
    """
    Validate a single row against the schema.
    Returns None if valid, or an error message string if invalid.
    
    Expected schema structure based on T006C:
    - row_index: integer
    - reason: string (error code)
    - original_smiles: string
    """
    required_fields = ['row_index', 'reason', 'original_smiles']
    
    # Check for missing fields
    for field in required_fields:
        if field not in row or row[field] is None:
            return f"Missing required field: {field}"
    
    # Validate row_index is an integer
    try:
        int(row['row_index'])
    except ValueError:
        return f"row_index is not an integer: {row['row_index']}"
    
    # Validate reason is not empty
    if not row['reason'] or not str(row['reason']).strip():
        return "reason field is empty"
    
    # Validate original_smiles is not empty
    if not row['original_smiles'] or not str(row['original_smiles']).strip():
        return "original_smiles field is empty"
    
    return None

def validate_exclusion_log(
    input_path: Path,
    schema_path: Path,
    output_path: Path,
    logger: logging.Logger
) -> bool:
    """
    Load the exclusion log, validate each row against the schema,
    and write a validation report.
    
    Returns True if all rows are valid, False otherwise.
    """
    logger.info(f"Loading exclusion log from: {input_path}")
    logger.info(f"Loading schema from: {input_path}")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return False
    
    schema = load_schema(schema_path)
    logger.info(f"Schema loaded successfully: {schema}")
    
    valid_count = 0
    invalid_count = 0
    errors = []
    
    with open(input_path, 'r', newline='') as infile:
        reader = csv.DictReader(infile)
        
        # Verify header matches expected schema
        expected_headers = ['row_index', 'reason', 'original_smiles']
        if reader.fieldnames != expected_headers:
            logger.warning(f"Header mismatch. Expected: {expected_headers}, Got: {reader.fieldnames}")
            # Continue validation but log the warning
        
        for idx, row in enumerate(reader):
            error = validate_row(row, schema)
            if error:
                invalid_count += 1
                errors.append({
                    'row_index': idx,
                    'error': error,
                    'row_data': row
                })
                logger.error(f"Row {idx} validation failed: {error}")
            else:
                valid_count += 1
    
    # Write validation report
    logger.info(f"Validation complete. Valid: {valid_count}, Invalid: {invalid_count}")
    
    with open(output_path, 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=['row_index', 'validation_status', 'error_message'])
        writer.writeheader()
        
        # Write summary
        writer.writerow({
            'row_index': 'SUMMARY',
            'validation_status': 'COMPLETE',
            'error_message': f"Total rows: {valid_count + invalid_count}, Valid: {valid_count}, Invalid: {invalid_count}"
        })
        
        # Write individual results
        for error_entry in errors:
            writer.writerow({
                'row_index': error_entry['row_index'],
                'validation_status': 'INVALID',
                'error_message': error_entry['error']
            })
        
        # Write valid rows (optional, for completeness)
        # In a full implementation, we might want to list valid rows too
    
    success = invalid_count == 0
    if success:
        logger.info("All rows validated successfully.")
    else:
        logger.error(f"Validation failed for {invalid_count} rows.")
    
    return success

def main():
    """Main entry point for the exclusion log schema validation."""
    parser = argparse.ArgumentParser(description="Validate exclusion log against schema")
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/exclusion_raw.log',
        help='Path to the exclusion log file'
    )
    parser.add_argument(
        '--schema',
        type=str,
        default='specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml',
        help='Path to the schema YAML file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/exclusion_validation.log',
        help='Path to write the validation report'
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    schema_path = Path(args.schema)
    output_path = Path(args.output)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger = setup_validation_logger(output_path.parent / 'validation.log')
    logger.info("Starting exclusion log schema validation")
    
    try:
        success = validate_exclusion_log(input_path, schema_path, output_path, logger)
        
        if not success:
            logger.error("Validation failed. Exiting with code 1.")
            sys.exit(1)
        else:
            logger.info("Validation passed. Exiting with code 0.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
