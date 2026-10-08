"""
Data validation utilities for molecular conductivity pipeline.
Implements schema validation for CSV and JSON files against YAML schemas.
"""
import logging
import sys
import os
import json
import argparse
import re
import csv
import yaml
from typing import Dict, Any, List, Optional, Set

# Configure logging
logger = logging.getLogger(__name__)

def validate_smiles(smiles_str: str) -> bool:
    """Validate a SMILES string using RDKit."""
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles_str)
        return mol is not None
    except Exception as e:
        logger.debug(f"SMILES validation failed for '{smiles_str}': {e}")
        return False

def check_target_range(values: List[float], min_log_range: float = 3.0) -> bool:
    """Check if target values span at least min_log_range orders of magnitude."""
    valid_values = [v for v in values if v is not None and not (isinstance(v, float) and (v != v))]
    if len(valid_values) < 2:
        return False
    try:
        log_values = [np.log10(v) for v in valid_values if v > 0]
        if len(log_values) < 2:
            return False
        return (max(log_values) - min(log_values)) >= min_log_range
    except Exception as e:
        logger.error(f"Target range check failed: {e}")
        return False

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_against_schema(csv_path: str, schema: Dict[str, Any]) -> bool:
    """Validate a CSV file against a schema definition."""
    required_columns = set(schema.get('required_columns', []))
    if not required_columns:
        logger.warning("Schema has no required_columns defined")
        return True

    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return False

    try:
        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                logger.error("CSV file is empty or has no header")
                return False

            actual_columns = set(reader.fieldnames)
            missing = required_columns - actual_columns

            if missing:
                logger.error(f"Missing required columns in {csv_path}: {missing}")
                return False

            # Validate row count
            row_count = sum(1 for _ in reader)
            if row_count == 0:
                logger.warning(f"CSV file {csv_path} has no data rows")
            else:
                logger.info(f"CSV validation passed: {row_count} rows, all required columns present")
            return True

    except Exception as e:
        logger.error(f"Error validating CSV {csv_path}: {e}")
        return False

def validate_json_against_schema(json_path: str, schema: Dict[str, Any]) -> bool:
    """Validate a JSON file against a schema definition."""
    required_fields = set(schema.get('required_fields', []))
    if not required_fields:
        logger.warning("Schema has no required_fields defined")
        return True

    if not os.path.exists(json_path):
        logger.error(f"JSON file not found: {json_path}")
        return False

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, dict):
            logger.error(f"JSON root must be an object (dict), got {type(data)}")
            return False

        actual_fields = set(data.keys())
        missing = required_fields - actual_fields

        if missing:
            logger.error(f"Missing required fields in {json_path}: {missing}")
            return False

        logger.info(f"JSON validation passed: all {len(required_fields)} required fields present")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {json_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating JSON {json_path}: {e}")
        return False

def validate_file(file_path: str, schema_path: str) -> bool:
    """Validate a file (CSV or JSON) against a schema."""
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.csv':
        return validate_csv_against_schema(file_path, schema)
    elif ext == '.json':
        return validate_json_against_schema(file_path, schema)
    else:
        logger.error(f"Unsupported file extension: {ext}. Expected .csv or .json")
        return False

def main():
    """CLI interface for file validation."""
    parser = argparse.ArgumentParser(description='Validate data files against schemas')
    parser.add_argument('--validate', required=True, help='Path to the data file to validate')
    parser.add_argument('--schema', required=True, help='Path to the schema YAML file')
    args = parser.parse_args()

    success = validate_file(args.validate, args.schema)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    main()
