"""
Contract validation module.
Implements T005a: Validate data against schema contracts.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import yaml

class SchemaValidationError(Exception):
    """Exception for schema validation errors."""
    pass

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load schema from YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def get_available_schemas(contracts_dir: Path) -> List[Path]:
    """Get list of available schema files."""
    return list(contracts_dir.glob("*.yaml"))

def validate_column_exists(df: pd.DataFrame, column: str) -> bool:
    """Check if column exists in DataFrame."""
    return column in df.columns

def validate_column_type(df: pd.DataFrame, column: str, expected_type: str) -> bool:
    """Validate column type."""
    if column not in df.columns:
        return False
    
    dtype = df[column].dtype
    type_map = {
        'int': (int, np.integer),
        'float': (float, np.floating),
        'str': (str, object),
        'bool': (bool, np.bool_)
    }
    
    expected = type_map.get(expected_type, (object,))
    return isinstance(df[column].iloc[0], expected) if len(df) > 0 else True

def validate_no_nulls(df: pd.DataFrame, column: str) -> bool:
    """Check for null values in column."""
    return df[column].isnull().sum() == 0

def validate_column_range(df: pd.DataFrame, column: str, min_val: float, max_val: float) -> bool:
    """Validate column values are within range."""
    if column not in df.columns:
        return False
    return df[column].between(min_val, max_val).all()

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate DataFrame against schema.
    Implements T005a.
    """
    errors = []
    columns = schema.get('columns', [])
    
    for col_spec in columns:
        col_name = col_spec.get('name')
        col_type = col_spec.get('type')
        required = col_spec.get('required', False)
        
        # Check existence
        if not validate_column_exists(df, col_name):
            if required:
                errors.append(f"Missing required column: {col_name}")
            continue
        
        # Check type
        if col_type and not validate_column_type(df, col_name, col_type):
            errors.append(f"Column {col_name} has wrong type")
        
        # Check nulls
        if required and not validate_no_nulls(df, col_name):
            errors.append(f"Column {col_name} contains null values")
    
    return len(errors) == 0, errors

def validate_dataframe_against_contract(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """Validate DataFrame against a contract schema."""
    is_valid, errors = validate_schema(df, schema)
    if not is_valid:
        for error in errors:
            print(f"Validation error: {error}")
    return is_valid

def validate_all_contracts(df: pd.DataFrame, contracts_dir: Path) -> bool:
    """Validate against all contracts in directory."""
    schemas = get_available_schemas(contracts_dir)
    all_valid = True
    
    for schema_path in schemas:
        schema = load_schema(schema_path)
        if not validate_dataframe_against_contract(df, schema):
            all_valid = False
    
    return all_valid

def main():
    """Main entry point for validation."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to data file")
    parser.add_argument("--contracts", default="code/specs/contracts", help="Contracts directory")
    parser.add_argument("--format", choices=['parquet', 'csv'], default='parquet')
    args = parser.parse_args()
    
    # Load data
    if args.format == 'parquet':
        df = pd.read_parquet(args.data)
    else:
        df = pd.read_csv(args.data)
    
    # Validate
    contracts_path = Path(args.contracts)
    if validate_all_contracts(df, contracts_path):
        print("All contracts validated successfully")
        sys.exit(0)
    else:
        print("Contract validation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()