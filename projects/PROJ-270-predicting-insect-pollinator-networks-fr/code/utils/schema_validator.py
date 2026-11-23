"""
Schema validation utilities for dataset outputs.
"""
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

from utils.logger import get_logger

logger = get_logger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema definition.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary representation of the schema.
    """
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def load_output_data(data_path: Path) -> List[Dict[str, Any]]:
    """
    Load output data from a CSV file.
    
    Args:
        data_path: Path to the CSV file.
        
    Returns:
        List of dictionaries representing rows.
    """
    import csv
    data = []
    with open(data_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def validate_structure(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> bool:
    """
    Validate that data matches the expected schema structure.
    
    Args:
        data: List of data records.
        schema: Schema definition.
        
    Returns:
        True if valid, False otherwise.
    """
    if not data:
        logger.warning("Data is empty, skipping structure validation.")
        return True
        
    expected_columns = schema.get("columns", [])
    if not expected_columns:
        logger.warning("Schema has no columns defined.")
        return True
        
    first_row = data[0]
    actual_columns = set(first_row.keys())
    expected_set = set(expected_columns)
    
    missing = expected_set - actual_columns
    if missing:
        logger.error(f"Missing columns in data: {missing}")
        return False
        
    extra = actual_columns - expected_set
    if extra:
        logger.warning(f"Extra columns in data (not in schema): {extra}")
        
    logger.info("Structure validation passed.")
    return True

def validate_schema(data_path: Path, schema_path: Path) -> bool:
    """
    Validate a dataset against its schema.
    
    Args:
        data_path: Path to the dataset CSV.
        schema_path: Path to the schema YAML.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        schema = load_schema(schema_path)
        data = load_output_data(data_path)
        return validate_structure(data, schema)
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False

def main():
    """CLI entry point for schema validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate dataset against schema")
    parser.add_argument("--data", required=True, help="Path to data CSV")
    parser.add_argument("--schema", required=True, help="Path to schema YAML")
    
    args = parser.parse_args()
    
    is_valid = validate_schema(Path(args.data), Path(args.schema))
    if is_valid:
        print("Validation successful.")
    else:
        print("Validation failed.")
        
    return 0 if is_valid else 1

if __name__ == "__main__":
    exit(main())
