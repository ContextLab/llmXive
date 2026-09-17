"""
CLI tool to enforce schema contracts on ingestion.

Validates CSV or JSON artifacts against their respective YAML schema contracts.
Supports dataset, regression, and sensitivity schema types.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import yaml

# Import logging helper from the project's utility module
from src.utils.io_helpers import setup_logging

logger = setup_logging("validate")


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_csv_artifact(
    file_path: Path,
    schema_path: Path,
    schema_type: str,
    strict: bool = True
) -> bool:
    """
    Validate a CSV artifact against a dataset schema.
    
    Args:
        file_path: Path to the CSV file to validate.
        schema_path: Path to the YAML schema definition.
        schema_type: Type of schema ('dataset', 'regression', 'sensitivity').
        strict: If True, fail on missing columns or type mismatches.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if schema_type not in ['dataset', 'sensitivity']:
        logger.error(f"Invalid schema_type for CSV: {schema_type}")
        return False

    logger.info(f"Validating CSV: {file_path} against schema: {schema_path}")
    
    if not file_path.exists():
        logger.error(f"Input file not found: {file_path}")
        return False

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return False

    # Dataset schema validation logic
    if schema_type == 'dataset':
        required_columns = schema.get('required_columns', [])
        column_types = schema.get('column_types', {})
        
        # Check columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            msg = f"Missing required columns: {missing_cols}"
            if strict:
                logger.error(msg)
                return False
            else:
                logger.warning(msg)
        
        # Check types (basic check)
        for col, expected_type in column_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                # Simple mapping check
                type_map = {
                    'int': ['int64', 'int32'],
                    'float': ['float64', 'float32'],
                    'str': ['object', 'string'],
                    'bool': ['bool']
                }
                if expected_type in type_map:
                    if actual_type not in type_map[expected_type]:
                        msg = f"Column '{col}' expected {expected_type}, got {actual_type}"
                        if strict:
                            logger.error(msg)
                            return False
                        else:
                            logger.warning(msg)
        
        logger.info(f"CSV validation passed: {len(df)} rows, {len(df.columns)} columns")
        return True

    # Sensitivity schema validation logic
    elif schema_type == 'sensitivity':
        required_columns = ['threshold', 'model', 'coefficient', 'p_value', 'std_err']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            msg = f"Missing required columns for sensitivity: {missing_cols}"
            if strict:
                logger.error(msg)
                return False
            else:
                logger.warning(msg)
        else:
            logger.info("Sensitivity CSV validation passed")
            return True

    return False


def validate_json_artifact(
    file_path: Path,
    schema_path: Path,
    schema_type: str,
    strict: bool = True
) -> bool:
    """
    Validate a JSON artifact against a regression schema.
    
    Args:
        file_path: Path to the JSON file to validate.
        schema_path: Path to the YAML schema definition.
        schema_type: Type of schema ('regression').
        strict: If True, fail on missing keys or type mismatches.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if schema_type != 'regression':
        logger.error(f"Invalid schema_type for JSON: {schema_type}")
        return False

    logger.info(f"Validating JSON: {file_path} against schema: {schema_path}")
    
    if not file_path.exists():
        logger.error(f"Input file not found: {file_path}")
        return False

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read JSON: {e}")
        return False

    # Regression schema validation logic
    required_keys = ['coefficients', 'p_values', 'vif_scores', 'model_type', 'collinearity_warning', 'aggregation_warning']
    missing_keys = [key for key in required_keys if key not in data]
    
    if missing_keys:
        msg = f"Missing required keys in JSON: {missing_keys}"
        if strict:
            logger.error(msg)
            return False
        else:
            logger.warning(msg)
    else:
        # Basic type checks
        if not isinstance(data.get('coefficients'), dict):
            if strict:
                logger.error("'coefficients' must be a dictionary")
                return False
            else:
                logger.warning("'coefficients' is not a dictionary")
        
        if not isinstance(data.get('model_type'), str):
            if strict:
                logger.error("'model_type' must be a string")
                return False
            else:
                logger.warning("'model_type' is not a string")

        logger.info("JSON validation passed")
        return True

    return False


def main():
    """Main entry point for the validation CLI."""
    parser = argparse.ArgumentParser(
        description="Validate data artifacts against schema contracts."
    )
    parser.add_argument(
        "--schema-type",
        type=str,
        required=True,
        choices=['dataset', 'regression', 'sensitivity'],
        help="Type of schema to validate against (dataset, regression, sensitivity)."
    )
    parser.add_argument(
        "file_path",
        type=Path,
        help="Path to the file to validate (CSV or JSON)."
    )
    parser.add_argument(
        "--contract",
        type=Path,
        required=True,
        help="Path to the YAML schema contract file."
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Do not fail on warnings; only fail on critical errors."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help="Logging level."
    )

    args = parser.parse_args()

    # Re-setup logging with user-specified level
    global logger
    logger = setup_logging("validate", level=args.log_level)

    if args.file_path.suffix.lower() == '.csv':
        success = validate_csv_artifact(
            args.file_path, args.contract, args.schema_type, strict=not args.no_strict
        )
    elif args.file_path.suffix.lower() == '.json':
        success = validate_json_artifact(
            args.file_path, args.contract, args.schema_type, strict=not args.no_strict
        )
    else:
        logger.error(f"Unsupported file type: {args.file_path.suffix}")
        sys.exit(1)

    if success:
        logger.info("Validation successful.")
        sys.exit(0)
    else:
        logger.error("Validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()