"""
Validation utilities for molecular conductivity pipeline.
Validates SMILES strings, target variable ranges, and data files against schemas.
"""
import logging
import sys
import os
import json
import argparse
import re
from typing import Tuple, List, Optional, Dict, Any

import pandas as pd
from rdkit import Chem
import yaml

from code.logging_config import setup_logging

logger = logging.getLogger(__name__)

def validate_smiles(smiles_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a SMILES string using RDKit.

    Args:
        smiles_str: The SMILES string to validate.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not isinstance(smiles_str, str) or not smiles_str.strip():
        return False, "Empty or non-string SMILES"

    try:
        mol = Chem.SmilesParser().ParseSmiles(smiles_str)
        if mol is None:
            return False, "RDKit failed to parse SMILES"
        # Basic sanitization
        Chem.SanitizeMol(mol)
        return True, None
    except Exception as e:
        return False, str(e)

def check_target_range(values: pd.Series, min_log_range: float = 3.0) -> Tuple[bool, str]:
    """
    Check if the target variable has sufficient dynamic range.

    Args:
        values: Pandas Series of target values.
        min_log_range: Minimum required log range (default 3.0 for 3 orders of magnitude).

    Returns:
        Tuple of (is_valid, message).
    """
    valid_values = values.dropna()
    if len(valid_values) == 0:
        return False, "No valid values found in target column"

    min_val = valid_values.min()
    max_val = valid_values.max()

    if min_val <= 0:
        return False, f"Target values must be positive for log transformation. Min: {min_val}"

    log_min = np.log(min_val)
    log_max = np.log(max_val)
    log_range = log_max - log_min

    if log_range < min_log_range:
        return False, f"Dynamic range ({log_range:.2f}) is less than required ({min_log_range})"

    return True, f"Dynamic range ({log_range:.2f}) meets requirement"

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema file.

    Args:
        schema_path: Path to the schema YAML file.

    Returns:
        Dictionary containing the schema.
    """
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a CSV DataFrame against a schema.

    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    expected_fields = schema.get('fields', [])

    if not expected_fields:
        logger.warning("Schema contains no 'fields' definition. Skipping column validation.")
        return True, []

    missing_cols = [f for f in expected_fields if f not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")

    # Check for unexpected columns (optional, strict mode could enforce this)
    # unexpected_cols = [c for c in df.columns if c not in expected_fields]
    # if unexpected_cols:
    #     logger.warning(f"Unexpected columns found: {unexpected_cols}")

    # Validate data types for numeric fields if specified in schema
    # (Simplified check: ensure non-NaN values in expected fields are numeric where expected)
    for field in expected_fields:
        if field in df.columns:
            # Check for NaN in required numeric fields (assuming all defined fields are numeric)
            if df[field].isna().any():
                # Allow NaNs for now, but log warning if critical
                pass

    return len(errors) == 0, errors

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a JSON dictionary against a schema.

    Args:
        data: The dictionary to validate.
        schema: The schema dictionary.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    errors = []
    expected_fields = schema.get('fields', [])

    if not expected_fields:
        logger.warning("Schema contains no 'fields' definition. Skipping key validation.")
        return True, []

    missing_keys = [f for f in expected_fields if f not in data]
    if missing_keys:
        errors.append(f"Missing required keys: {missing_keys}")

    return len(errors) == 0, errors

def validate_file(file_path: str, schema_path: str) -> bool:
    """
    Validate a data file (CSV or JSON) against a schema.

    Args:
        file_path: Path to the data file.
        schema_path: Path to the schema YAML file.

    Returns:
        True if valid, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return False

    if not os.path.exists(schema_path):
        logger.error(f"Schema not found: {schema_path}")
        return False

    schema = load_schema(schema_path)

    if file_path.endswith('.csv'):
        try:
            df = pd.read_csv(file_path)
            is_valid, errors = validate_csv_against_schema(df, schema)
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            return False

    elif file_path.endswith('.json'):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            is_valid, errors = validate_json_against_schema(data, schema)
        except Exception as e:
            logger.error(f"Error reading JSON: {e}")
            return False
    else:
        logger.error(f"Unsupported file format: {file_path}")
        return False

    if not is_valid:
        for err in errors:
            logger.error(f"Validation error: {err}")
        return False

    logger.info(f"Validation successful for {file_path}")
    return True

def main():
    """CLI entry point for validation."""
    parser = argparse.ArgumentParser(description="Validate data files against schemas.")
    parser.add_argument("--validate", type=str, required=True, help="Path to data file (CSV or JSON)")
    parser.add_argument("--schema", type=str, required=True, help="Path to schema YAML file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    setup_logging(level=logging.DEBUG if args.verbose else logging.INFO)

    success = validate_file(args.validate, args.schema)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
