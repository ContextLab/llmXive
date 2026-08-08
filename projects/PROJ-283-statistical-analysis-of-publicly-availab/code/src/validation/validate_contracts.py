import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def get_available_schemas(contracts_dir: str = 'specs/contracts') -> List[str]:
    """Get list of available schema files."""
    contracts_path = Path(contracts_dir)
    if not contracts_path.exists():
        return []
    
    return [str(f) for f in contracts_path.glob('*.yaml')]

def validate_column_exists(df: pd.DataFrame, column: str) -> bool:
    """Validate that a column exists in the DataFrame."""
    if column not in df.columns:
        raise SchemaValidationError(f"Missing required column: {column}")
    return True

def validate_column_type(df: pd.DataFrame, column: str, expected_type: str) -> bool:
    """Validate that a column has the expected type."""
    if column not in df.columns:
        raise SchemaValidationError(f"Column {column} not found for type validation")
    
    actual_type = str(df[column].dtype)
    
    # Map expected types to pandas dtypes
    type_mapping = {
        'integer': ['int64', 'int32', 'int16', 'int8'],
        'float': ['float64', 'float32'],
        'string': ['object', 'string'],
        'boolean': ['bool']
    }
    
    expected_types = type_mapping.get(expected_type.lower(), [expected_type])
    
    if actual_type not in expected_types:
        raise SchemaValidationError(
            f"Column {column} has type {actual_type}, expected one of {expected_types}"
        )
    return True

def validate_no_nulls(df: pd.DataFrame, column: str) -> bool:
    """Validate that a column has no null values."""
    if column not in df.columns:
        raise SchemaValidationError(f"Column {column} not found for null validation")
    
    if df[column].isnull().any():
        null_count = df[column].isnull().sum()
        raise SchemaValidationError(f"Column {column} contains {null_count} null values")
    return True

def validate_column_range(df: pd.DataFrame, column: str, min_val: float = None, max_val: float = None) -> bool:
    """Validate that a column values are within range."""
    if column not in df.columns:
        raise SchemaValidationError(f"Column {column} not found for range validation")
    
    if min_val is not None and df[column].min() < min_val:
        raise SchemaValidationError(
            f"Column {column} has minimum value {df[column].min()}, expected >= {min_val}"
        )
    
    if max_val is not None and df[column].max() > max_val:
        raise SchemaValidationError(
            f"Column {column} has maximum value {df[column].max()}, expected <= {max_val}"
        )
    
    return True

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate a DataFrame against a schema.
    
    Args:
        df: DataFrame to validate
        schema: Schema dictionary
    
    Returns:
        True if validation passes
    
    Raises:
        SchemaValidationError: If validation fails
    """
    if 'columns' not in schema:
        raise SchemaValidationError("Schema must contain 'columns' definition")
    
    for col_def in schema['columns']:
        col_name = col_def['name']
        
        # Check column exists
        validate_column_exists(df, col_name)
        
        # Check type
        if 'type' in col_def:
            validate_column_type(df, col_name, col_def['type'])
        
        # Check for nulls if required
        if col_def.get('required', False):
            validate_no_nulls(df, col_name)
        
        # Check range if specified
        if 'min' in col_def or 'max' in col_def:
            validate_column_range(
                df, col_name,
                min_val=col_def.get('min'),
                max_val=col_def.get('max')
            )
    
    return True

def validate_dataframe_against_contract(df: pd.DataFrame, contract_path: str) -> bool:
    """Validate a DataFrame against a contract file."""
    schema = load_schema(contract_path)
    return validate_schema(df, schema)

def validate_all_contracts(df: pd.DataFrame, contracts_dir: str = 'specs/contracts') -> List[str]:
    """Validate a DataFrame against all contracts in a directory."""
    schemas = get_available_schemas(contracts_dir)
    results = []
    
    for schema_path in schemas:
        try:
            validate_dataframe_against_contract(df, schema_path)
            results.append(f"✓ {schema_path}")
        except SchemaValidationError as e:
            results.append(f"✗ {schema_path}: {e}")
    
    return results

def main():
    """Main entry point for the validation script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate data against schema contracts')
    parser.add_argument('--data', type=str, required=True, help='Input data file (parquet or csv)')
    parser.add_argument('--contracts', type=str, default=None, help='Specific contract file to validate against')
    parser.add_argument('--format', type=str, choices=['parquet', 'csv'], default='parquet', help='Input data format')
    
    args = parser.parse_args()
    
    try:
        # Load data
        data_path = Path(args.data)
        if args.format == 'parquet' or data_path.suffix == '.parquet':
            df = pd.read_parquet(data_path)
        elif args.format == 'csv' or data_path.suffix == '.csv':
            df = pd.read_csv(data_path)
        else:
            raise ValueError(f"Unsupported file format: {data_path.suffix}")
        
        logger.info(f"Loaded {len(df)} rows from {args.data}")
        
        # Validate
        if args.contracts:
            # Validate against specific contract
            validate_dataframe_against_contract(df, args.contracts)
            logger.info(f"Validation passed for {args.contracts}")
        else:
            # Validate against all contracts
            results = validate_all_contracts(df)
            for result in results:
                logger.info(result)
            
            if any(r.startswith('✗') for r in results):
                raise SchemaValidationError("Some validations failed")
            else:
                logger.info("All validations passed")
        
        sys.exit(0)
    except SchemaValidationError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()