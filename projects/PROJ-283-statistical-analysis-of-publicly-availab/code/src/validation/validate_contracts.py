import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Loads a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def get_available_schemas() -> List[Path]:
    """Returns a list of available schema files."""
    contracts_dir = Path("specs/contracts")
    if not contracts_dir.exists():
        return []
    return list(contracts_dir.glob("*.schema.yaml"))

def validate_column_exists(df: pd.DataFrame, column_name: str) -> None:
    """Validates that a column exists in the dataframe."""
    if column_name not in df.columns:
        raise SchemaValidationError(f"Missing required column: {column_name}")

def validate_column_type(df: pd.DataFrame, column_name: str, expected_type: str) -> None:
    """Validates that a column has the expected dtype."""
    # Map schema types to pandas dtypes
    type_map = {
        'int': ['int64', 'int32'],
        'float': ['float64', 'float32'],
        'string': ['object', 'string'],
        'bool': ['bool']
    }
    
    expected_pandas_types = type_map.get(expected_type, [expected_type])
    actual_dtype = str(df[column_name].dtype)
    
    # Check if actual dtype is in the allowed list
    is_valid = False
    for t in expected_pandas_types:
        if t in actual_dtype:
            is_valid = True
            break
    
    if not is_valid:
        raise SchemaValidationError(
            f"Column '{column_name}' has dtype '{actual_dtype}', expected one of {expected_pandas_types}"
        )

def validate_no_nulls(df: pd.DataFrame, column_name: str) -> None:
    """Validates that a column has no null values."""
    if df[column_name].isnull().any():
        null_count = df[column_name].isnull().sum()
        raise SchemaValidationError(
            f"Column '{column_name}' contains {null_count} null values"
        )

def validate_column_range(df: pd.DataFrame, column_name: str, min_val: float, max_val: float) -> None:
    """Validates that a column's values are within a specified range."""
    if df[column_name].min() < min_val or df[column_name].max() > max_val:
        raise SchemaValidationError(
            f"Column '{column_name}' values out of range [{min_val}, {max_val}]"
        )

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> None:
    """Validates a dataframe against a schema definition."""
    if 'columns' not in schema:
        raise SchemaValidationError("Invalid schema: missing 'columns' definition")
    
    for col_def in schema['columns']:
        col_name = col_def['name']
        
        # 1. Check existence
        validate_column_exists(df, col_name)
        
        # 2. Check type
        if 'type' in col_def:
            validate_column_type(df, col_name, col_def['type'])
        
        # 3. Check nulls
        if col_def.get('nullable') is False:
            validate_no_nulls(df, col_name)
        
        # 4. Check range
        if 'min' in col_def or 'max' in col_def:
            min_val = col_def.get('min', float('-inf'))
            max_val = col_def.get('max', float('inf'))
            validate_column_range(df, col_name, min_val, max_val)

def validate_dataframe_against_contract(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Main validation function.
    Returns True if valid, raises SchemaValidationError if invalid.
    """
    try:
        validate_schema(df, schema)
        return True
    except SchemaValidationError:
        raise

def validate_all_contracts(dataframes: Dict[str, pd.DataFrame], contracts_dir: Path = None) -> bool:
    """Validates multiple dataframes against their corresponding contracts."""
    if contracts_dir is None:
        contracts_dir = Path("specs/contracts")
    
    if not contracts_dir.exists():
        raise FileNotFoundError(f"Contracts directory not found: {contracts_dir}")
    
    for schema_file in contracts_dir.glob("*.schema.yaml"):
        schema_name = schema_file.stem.replace('.schema', '')
        if schema_name not in dataframes:
            logger = logging.getLogger(__name__)
            logger.warning(f"No dataframe found for schema {schema_name}, skipping.")
            continue
        
        schema = load_schema(schema_file)
        validate_dataframe_against_contract(dataframes[schema_name], schema)
    
    return True

def main():
    """
    CLI entry point for validation.
    Usage: python src/validation/validate_contracts.py --data <path> --schema <path> [--format parquet|csv]
    """
    import argparse
    import logging
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    parser = argparse.ArgumentParser(description="Validate DataFrame against a schema")
    parser.add_argument('--data', type=str, required=True, help="Path to the data file (CSV or Parquet)")
    parser.add_argument('--schema', type=str, required=True, help="Path to the schema YAML file")
    parser.add_argument('--format', type=str, choices=['parquet', 'csv'], default='parquet', help="Data format")
    
    args = parser.parse_args()
    
    data_path = Path(args.data)
    schema_path = Path(args.schema)
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)
    
    try:
        # Load data
        if args.format == 'parquet':
            df = pd.read_parquet(data_path)
        else:
            df = pd.read_csv(data_path)
        
        # Load schema
        schema = load_schema(schema_path)
        
        # Validate
        validate_dataframe_against_contract(df, schema)
        
        logger.info("Validation PASSED")
        sys.exit(0)
        
    except SchemaValidationError as e:
        logger.error("Validation Failed")
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()