import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import yaml
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaValidationError(Exception):
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def get_available_schemas(contracts_dir: str) -> List[str]:
    """List all available schema files."""
    contracts_path = Path(contracts_dir)
    if not contracts_path.exists():
        return []
    return [str(f) for f in contracts_path.glob("*.yaml")]

def validate_column_exists(df: pd.DataFrame, column: str, schema_name: str) -> None:
    if column not in df.columns:
        raise SchemaValidationError(f"Column '{column}' missing in {schema_name} validation.")

def validate_column_type(df: pd.DataFrame, column: str, expected_type: str, schema_name: str) -> None:
    # Basic type checking
    if expected_type == 'integer':
        if not pd.api.types.is_integer_dtype(df[column]) and not pd.api.types.is_numeric_dtype(df[column]):
            raise SchemaValidationError(f"Column '{column}' in {schema_name} is not numeric.")
    elif expected_type == 'string':
        if not pd.api.types.is_string_dtype(df[column]) and not pd.api.types.is_object_dtype(df[column]):
            raise SchemaValidationError(f"Column '{column}' in {schema_name} is not string.")
    elif expected_type == 'float':
        if not pd.api.types.is_float_dtype(df[column]):
            raise SchemaValidationError(f"Column '{column}' in {schema_name} is not float.")

def validate_no_nulls(df: pd.DataFrame, column: str, schema_name: str) -> None:
    if df[column].isnull().any():
        raise SchemaValidationError(f"Column '{column}' in {schema_name} contains null values.")

def validate_column_range(df: pd.DataFrame, column: str, min_val: float, max_val: float, schema_name: str) -> None:
    if df[column].min() < min_val or df[column].max() > max_val:
        raise SchemaValidationError(f"Column '{column}' in {schema_name} out of range [{min_val}, {max_val}].")

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any], schema_name: str) -> None:
    """Validate a DataFrame against a schema definition."""
    if 'columns' not in schema:
        logger.warning(f"Schema {schema_name} has no 'columns' definition.")
        return

    for col_def in schema['columns']:
        col_name = col_def['name']
        validate_column_exists(df, col_name, schema_name)
        
        if 'type' in col_def:
            validate_column_type(df, col_name, col_def['type'], schema_name)
        
        if 'required' in col_def and col_def['required']:
            validate_no_nulls(df, col_name, schema_name)
        
        if 'min' in col_def or 'max' in col_def:
            min_val = col_def.get('min', -float('inf'))
            max_val = col_def.get('max', float('inf'))
            validate_column_range(df, col_name, min_val, max_val, schema_name)

def validate_dataframe_against_contract(df: pd.DataFrame, schema_path: str) -> bool:
    """Validate a DataFrame against a single contract file."""
    schema = load_schema(schema_path)
    schema_name = Path(schema_path).stem
    try:
        validate_schema(df, schema, schema_name)
        logger.info(f"Validation passed for {schema_name}.")
        return True
    except SchemaValidationError as e:
        logger.error(f"Validation failed for {schema_name}: {e}")
        return False

def validate_all_contracts(df: pd.DataFrame, contracts_dir: str) -> bool:
    """Validate a DataFrame against all contracts in a directory."""
    contracts = get_available_schemas(contracts_dir)
    if not contracts:
        logger.warning(f"No contracts found in {contracts_dir}.")
        return True
    
    all_valid = True
    for contract_path in contracts:
        if not validate_dataframe_against_contract(df, contract_path):
            all_valid = False
    return all_valid

def main():
    parser = argparse.ArgumentParser(description="Validate data against schema contracts.")
    parser.add_argument("--data", required=True, help="Path to the input data file (CSV or Parquet).")
    parser.add_argument("--contracts", default="specs/contracts", help="Path to the contracts directory.")
    parser.add_argument("--format", choices=["csv", "parquet"], default="parquet", help="Data format.")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.data):
        logger.error(f"Data file not found: {args.data}")
        sys.exit(1)
    
    # Load data
    if args.format == "csv":
        df = pd.read_csv(args.data)
    else:
        df = pd.read_parquet(args.data)
    
    logger.info(f"Loaded {len(df)} rows from {args.data}")
    
    # Validate
    if validate_all_contracts(df, args.contracts):
        logger.info("All validations passed.")
        sys.exit(0)
    else:
        logger.error("Validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
