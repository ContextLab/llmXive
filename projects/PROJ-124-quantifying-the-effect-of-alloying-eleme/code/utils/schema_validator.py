"""
Schema validation utilities for CSV and JSON files.
"""
import yaml
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger("utils.schema_validator")

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a schema definition.
    
    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary.
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    required_columns = schema.get("required_columns", [])
    column_types = schema.get("column_types", {})

    # Check required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # Check types (simplified)
    for col, expected_type in column_types.items():
        if col in df.columns:
            if expected_type == "numeric" and not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column {col} should be numeric but is {df[col].dtype}")
            elif expected_type == "string" and not pd.api.types.is_string_dtype(df[col]):
                errors.append(f"Column {col} should be string but is {df[col].dtype}")

    return len(errors) == 0, errors

def validate_processed_features(csv_path: str, schema_path: str) -> Tuple[bool, List[str]]:
    """Validate the processed features CSV against the schema."""
    try:
        schema = load_schema(schema_path)
        df = pd.read_csv(csv_path)
        return validate_csv_schema(df, schema)
    except Exception as e:
        return False, [f"Validation error: {str(e)}"]

def main():
    """Test the schema validator."""
    logger.info("Schema validator module loaded.")

if __name__ == "__main__":
    main()
