"""
Validate the generated performance metrics CSV against the JSON schema.

This script loads data/processed/performance_metrics.csv and validates it
against specs/001-explore-network-structure-superconducting-qubit-coupling/contracts/performance_metrics.schema.json.

It raises an error if validation fails or if the file is missing.
"""
import os
import sys
import csv
import json
import jsonschema
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "processed" / "performance_metrics.csv"
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-explore-network-structure-superconducting-qubit-coupling" / "contracts" / "performance_metrics.schema.json"

def load_csv_as_records(csv_path: Path) -> list:
    """Load a CSV file and return a list of dictionaries (records)."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    records = []
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields to numbers for validation
            # The schema expects numbers, not strings
            numeric_fields = ['t1_mean', 't2_mean', 'cx_error_mean', 'readout_error_mean']
            for field in numeric_fields:
                if field in row and row[field]:
                    try:
                        row[field] = float(row[field])
                    except ValueError:
                        logger.warning(f"Could not convert {field} '{row[field]}' to float, skipping row.")
                        row[field] = None
            
            # Handle timestamp validation (ISO format)
            if 'timestamp' in row and row['timestamp']:
                try:
                    datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Invalid timestamp format: {row['timestamp']}")
            
            records.append(row)
    
    return records

def load_schema(schema_path: Path) -> dict:
    """Load the JSON schema."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_records(records: list, schema: dict) -> bool:
    """
    Validate each record against the schema.
    Since jsonschema.validate expects a single object, we validate each row individually.
    """
    valid_count = 0
    error_count = 0
    
    for i, record in enumerate(records):
        try:
            jsonschema.validate(record, schema)
            valid_count += 1
        except jsonschema.ValidationError as e:
            error_count += 1
            logger.error(f"Validation error in row {i}: {e.message}")
            logger.debug(f"Row data: {record}")
    
    logger.info(f"Validation complete: {valid_count} valid, {error_count} invalid.")
    return error_count == 0

def main():
    """Main entry point."""
    logger.info(f"Starting validation of {CSV_PATH}")
    
    if not CSV_PATH.exists():
        logger.error(f"Input file missing: {CSV_PATH}")
        logger.error("Run the fetcher/generator first (e.g., python code/fetcher.py --save-snapshots and generate_calibration_csv.py)")
        sys.exit(1)
    
    if not SCHEMA_PATH.exists():
        logger.error(f"Schema file missing: {SCHEMA_PATH}")
        sys.exit(1)

    try:
        records = load_csv_as_records(CSV_PATH)
        if not records:
            logger.error("CSV file is empty or has no data rows.")
            sys.exit(1)
        
        schema = load_schema(SCHEMA_PATH)
        
        if validate_records(records, schema):
            logger.info("SUCCESS: All records validated successfully against the schema.")
            sys.exit(0)
        else:
            logger.error("FAILURE: One or more records failed schema validation.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()