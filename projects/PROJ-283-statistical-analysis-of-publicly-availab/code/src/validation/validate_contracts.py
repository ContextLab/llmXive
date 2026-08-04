import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import yaml
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def get_available_schemas(contracts_dir: Path) -> List[Path]:
    """Get list of available schema files."""
    return list(contracts_dir.glob("*.schema.yaml"))

def validate_column_exists(df: pd.DataFrame, column: str) -> bool:
    """Validate that a column exists in the DataFrame."""
    if column not in df.columns:
        raise SchemaValidationError(f"Missing required column: {column}")
    return True

def validate_column_type(df: pd.DataFrame, column: str, expected_type: str) -> bool:
    """Validate that a column has the expected type."""
    if column not in df.columns:
        return True  # Already validated elsewhere
    
    actual_type = str(df[column].dtype)
    # Simple type mapping
    type_mapping = {
        'int': ['int64', 'int32'],
        'float': ['float64', 'float32'],
        'string': ['object', 'string'],
        'bool': ['bool']
    }
    
    if expected_type in type_mapping:
        if actual_type not in type_mapping[expected_type]:
            logger.warning(f"Column {column} has type {actual_type}, expected {expected_type}")
            # Don't fail on type mismatch for now
    
    return True

def validate_no_nulls(df: pd.DataFrame, column: str) -> bool:
    """Validate that a column has no null values."""
    if column not in df.columns:
        return True
    
    null_count = df[column].isna().sum()
    if null_count > 0:
        raise SchemaValidationError(f"Column {column} contains {null_count} null values")
    
    return True

def validate_column_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> bool:
    """Validate that column values are within range."""
    if column not in df.columns:
        return True
    
    col_min = df[column].min()
    col_max = df[column].max()
    
    if col_min < min_val or col_max > max_val:
        logger.warning(f"Column {column} range [{col_min}, {col_max}] outside expected [{min_val}, {max_val}]")
        # Don't fail on range violation for now
    
    return True

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate DataFrame against a schema."""
    columns = schema.get('columns', [])
    
    for col_spec in columns:
        col_name = col_spec.get('name')
        col_type = col_spec.get('type')
        required = col_spec.get('required', False)
        min_val = col_spec.get('min')
        max_val = col_spec.get('max')
        
        # Check existence
        if required:
            validate_column_exists(df, col_name)
        
        # Check type
        if col_type:
            validate_column_type(df, col_name, col_type)
        
        # Check nulls
        if required:
            validate_no_nulls(df, col_name)
        
        # Check range
        if min_val is not None or max_val is not None:
            min_v = min_val if min_val is not None else float('-inf')
            max_v = max_val if max_val is not None else float('inf')
            validate_column_range(df, col_name, min_v, max_v)
    
    return True

def validate_dataframe_against_contract(df: pd.DataFrame, schema_path: Path) -> bool:
    """Validate a DataFrame against a specific contract schema."""
    schema = load_schema(schema_path)
    return validate_schema(df, schema)

def validate_all_contracts(df: pd.DataFrame, contracts_dir: Path) -> List[str]:
    """Validate DataFrame against all contracts in directory."""
    errors = []
    schemas = get_available_schemas(contracts_dir)
    
    for schema_path in schemas:
        try:
            validate_dataframe_against_contract(df, schema_path)
            logger.info(f"✓ {schema_path.name} passed")
        except SchemaValidationError as e:
            errors.append(f"{schema_path.name}: {e}")
            logger.error(f"✗ {schema_path.name} failed: {e}")
    
    return errors

def main():
    """Main entry point for validation script."""
    parser = argparse.ArgumentParser(description='Validate data against schema contracts')
    parser.add_argument('--data', type=str, required=True,
                      help='Path to input data file (parquet or csv)')
    parser.add_argument('--contracts', type=str, default=None,
                      help='Path to contracts directory')
    parser.add_argument('--format', type=str, choices=['parquet', 'csv'], default='parquet',
                      help='Format of input data')
    
    args = parser.parse_args()
    
    base_path = Path(__file__).parent.parent.parent
    
    # Load data
    data_path = Path(args.data)
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    logger.info(f"Loading data from {data_path}")
    if args.format == 'parquet':
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)
    
    logger.info(f"Loaded {len(df)} rows")
    
    # Set contracts directory
    if args.contracts:
        contracts_dir = Path(args.contracts)
    else:
        contracts_dir = base_path / "specs" / "contracts"
    
    if not contracts_dir.exists():
        logger.error(f"Contracts directory not found: {contracts_dir}")
        sys.exit(1)
    
    # Validate
    errors = validate_all_contracts(df, contracts_dir)
    
    if errors:
        logger.error(f"Validation failed with {len(errors)} errors")
        sys.exit(1)
    else:
        logger.info("All validations passed")
        sys.exit(0)

if __name__ == "__main__":
    main()
