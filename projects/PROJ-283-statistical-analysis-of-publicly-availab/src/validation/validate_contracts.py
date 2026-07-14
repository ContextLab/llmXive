"""
Contract validation module for chess data analysis pipeline.
Loads YAML schemas from specs/contracts/ and validates pandas DataFrames against them.
"""
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import yaml

# Custom exception for schema validation errors
class SchemaValidationError(Exception):
    """Raised when DataFrame validation against a schema fails."""
    pass

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a YAML schema file.
    
    Args:
        schema_path: Path to the YAML schema file
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        yaml.YAMLError: If YAML is malformed
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def get_available_schemas(contracts_dir: Path) -> List[Path]:
    """
    Get list of all schema files in the contracts directory.
    
    Args:
        contracts_dir: Path to the contracts directory
        
    Returns:
        List of paths to schema YAML files
    """
    if not contracts_dir.exists():
        return []
    
    return list(contracts_dir.glob("*.schema.yaml"))

def validate_column_exists(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that all required columns exist in the DataFrame.
    
    Args:
        df: DataFrame to validate
        schema: Schema definition dictionary
        
    Returns:
        Tuple of (is_valid, list_of_missing_columns)
    """
    required_columns = schema.get("required_columns", [])
    actual_columns = set(df.columns)
    missing = [col for col in required_columns if col not in actual_columns]
    return len(missing) == 0, missing

def validate_column_type(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that columns have the expected types.
    
    Args:
        df: DataFrame to validate
        schema: Schema definition dictionary
        
    Returns:
        Tuple of (is_valid, list_of_type_errors)
    """
    column_types = schema.get("column_types", {})
    errors = []
    
    for col, expected_type in column_types.items():
        if col not in df.columns:
            continue  # Will be caught by validate_column_exists
        
        actual_type = str(df[col].dtype)
        
        # Map common pandas dtypes to expected types
        type_mapping = {
            'int64': ['int', 'integer'],
            'float64': ['float', 'number'],
            'object': ['string', 'str'],
            'bool': ['boolean', 'bool'],
            'datetime64[ns]': ['datetime', 'date']
        }
        
        is_valid_type = False
        for pd_type, valid_names in type_mapping.items():
            if actual_type == pd_type and expected_type.lower() in valid_names:
                is_valid_type = True
                break
        
        if not is_valid_type:
            errors.append(f"Column '{col}' has type '{actual_type}', expected '{expected_type}'")
    
    return len(errors) == 0, errors

def validate_no_nulls(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that required columns have no null values.
    
    Args:
        df: DataFrame to validate
        schema: Schema definition dictionary
        
    Returns:
        Tuple of (is_valid, list_of_null_errors)
    """
    required_columns = schema.get("required_columns", [])
    errors = []
    
    for col in required_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                errors.append(f"Column '{col}' has {null_count} null values")
        
    return len(errors) == 0, errors

def validate_column_range(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that numeric columns are within expected ranges.
    
    Args:
        df: DataFrame to validate
        schema: Schema definition dictionary
        
    Returns:
        Tuple of (is_valid, list_of_range_errors)
    """
    range_constraints = schema.get("column_ranges", {})
    errors = []
    
    for col, constraints in range_constraints.items():
        if col not in df.columns:
            continue
        
        min_val = constraints.get("min")
        max_val = constraints.get("max")
        
        if min_val is not None:
            below_min = (df[col] < min_val).sum()
            if below_min > 0:
                errors.append(f"Column '{col}' has {below_min} values below minimum {min_val}")
        
        if max_val is not None:
            above_max = (df[col] > max_val).sum()
            if above_max > 0:
                errors.append(f"Column '{col}' has {above_max} values above maximum {max_val}")
    
    return len(errors) == 0, errors

def validate_schema(df: pd.DataFrame, schema: Dict[str, Any], schema_name: str = "unknown") -> Tuple[bool, List[str]]:
    """
    Run all validation checks against a schema.
    
    Args:
        df: DataFrame to validate
        schema: Schema definition dictionary
        schema_name: Name of the schema for error messages
        
    Returns:
        Tuple of (is_valid, list_of_all_errors)
    """
    all_errors = []
    
    # Check required columns
    valid, missing = validate_column_exists(df, schema)
    if not valid:
        all_errors.extend([f"Missing required column: {col}" for col in missing])
    
    # Skip type, null, and range checks if columns are missing
    if valid:
        valid, type_errors = validate_column_type(df, schema)
        if not valid:
            all_errors.extend(type_errors)
        
        valid, null_errors = validate_no_nulls(df, schema)
        if not valid:
            all_errors.extend(null_errors)
        
        valid, range_errors = validate_column_range(df, schema)
        if not valid:
            all_errors.extend(range_errors)
    
    return len(all_errors) == 0, all_errors

def validate_dataframe_against_contract(df: pd.DataFrame, schema_path: Path) -> bool:
    """
    Validate a DataFrame against a specific schema file.
    
    Args:
        df: DataFrame to validate
        schema_path: Path to the schema YAML file
        
    Returns:
        True if validation passes, False otherwise
        
    Raises:
        SchemaValidationError: If validation fails
    """
    schema_name = schema_path.stem
    schema = load_schema(schema_path)
    
    is_valid, errors = validate_schema(df, schema, schema_name)
    
    if not is_valid:
        error_msg = f"Validation failed for {schema_name}:\n" + "\n".join(f"  - {e}" for e in errors)
        raise SchemaValidationError(error_msg)
    
    return True

def validate_all_contracts(df: pd.DataFrame, contracts_dir: Path) -> Dict[str, bool]:
    """
    Validate DataFrame against all schema files in a directory.
    
    Args:
        df: DataFrame to validate
        contracts_dir: Path to the contracts directory
        
    Returns:
        Dictionary mapping schema names to validation status
    """
    results = {}
    schema_files = get_available_schemas(contracts_dir)
    
    for schema_file in schema_files:
        schema_name = schema_file.stem
        try:
            validate_dataframe_against_contract(df, schema_file)
            results[schema_name] = True
        except SchemaValidationError as e:
            results[schema_name] = False
            print(f"Warning: {schema_name} validation failed: {e}", file=sys.stderr)
    
    return results

def main():
    """
    Command-line interface for contract validation.
    Usage: python -m src.validation.validate_contracts --data <path> --contracts <dir>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate DataFrame against contract schemas")
    parser.add_argument("--data", type=str, required=True, help="Path to parquet or csv data file")
    parser.add_argument("--contracts", type=str, default="specs/contracts", help="Path to contracts directory")
    parser.add_argument("--format", type=str, default="parquet", choices=["parquet", "csv"], help="Data file format")
    
    args = parser.parse_args()
    
    # Load data
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: Data file not found: {data_path}", file=sys.stderr)
        sys.exit(1)
    
    if args.format == "parquet":
        df = pd.read_parquet(data_path)
    else:
        df = pd.read_csv(data_path)
    
    print(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    
    # Validate
    contracts_path = Path(args.contracts)
    results = validate_all_contracts(df, contracts_path)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\nValidation Results: {passed}/{total} schemas passed")
    for schema_name, status in results.items():
        status_str = "PASS" if status else "FAIL"
        print(f"  {schema_name}: {status_str}")
    
    if passed < total:
        sys.exit(1)
    else:
        print("\nAll validations passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
