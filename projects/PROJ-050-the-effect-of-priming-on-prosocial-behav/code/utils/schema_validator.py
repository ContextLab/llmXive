"""
Schema validation utilities for the prosocial behavior research pipeline.

Validates datasets against defined YAML schemas:
- dataset.schema.yaml (raw/processed data structure)
- scored.schema.yaml (scoring results structure)
- output.schema.yaml (analysis results structure)
"""
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml
import pandas as pd
from code.config import PROJECT_ROOT

# Configure logger
logger = logging.getLogger(__name__)

SCHEMA_DIR = PROJECT_ROOT / "specs" / "001-the-effect-of-priming-on-prosocial-behav"
SCHEMAS = {
    "dataset": "dataset.schema.yaml",
    "scored": "scored.schema.yaml",
    "output": "output.schema.yaml",
}

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema definition from the specs directory.
    
    Args:
        schema_name: One of 'dataset', 'scored', 'output'
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        FileNotFoundError: If schema file doesn't exist
        ValueError: If schema_name is invalid
    """
    if schema_name not in SCHEMAS:
        raise ValueError(f"Unknown schema: {schema_name}. Must be one of {list(SCHEMAS.keys())}")
    
    schema_path = SCHEMA_DIR / SCHEMAS[schema_name]
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_column_types(df: pd.DataFrame, expected_columns: Dict[str, str]) -> Tuple[bool, List[str]]:
    """
    Validate that DataFrame columns exist and have expected types.
    
    Args:
        df: DataFrame to validate
        expected_columns: Dict mapping column name to expected dtype string
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    for col, expected_dtype in expected_columns.items():
        if col not in df.columns:
            errors.append(f"Missing required column: '{col}'")
        else:
            actual_dtype = str(df[col].dtype)
            # Normalize dtype comparison
            if expected_dtype == "string" and not pd.api.types.is_string_dtype(df[col]):
                errors.append(f"Column '{col}' expected string type, got {actual_dtype}")
            elif expected_dtype == "integer" and not pd.api.types.is_integer_dtype(df[col]):
                errors.append(f"Column '{col}' expected integer type, got {actual_dtype}")
            elif expected_dtype == "float" and not pd.api.types.is_float_dtype(df[col]):
                errors.append(f"Column '{col}' expected float type, got {actual_dtype}")
            elif expected_dtype == "boolean" and not pd.api.types.is_bool_dtype(df[col]):
                errors.append(f"Column '{col}' expected boolean type, got {actual_dtype}")
            elif expected_dtype == "datetime" and not pd.api.types.is_datetime64_any_dtype(df[col]):
                errors.append(f"Column '{col}' expected datetime type, got {actual_dtype}")
    
    return len(errors) == 0, errors

def validate_schema(df: pd.DataFrame, schema_name: str) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a named schema.
    
    Args:
        df: DataFrame to validate
        schema_name: One of 'dataset', 'scored', 'output'
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    try:
        schema = load_schema(schema_name)
    except (FileNotFoundError, ValueError) as e:
        return False, [str(e)]
    
    errors = []
    
    # Validate required columns
    required_columns = schema.get("required_columns", {})
    is_valid, col_errors = validate_column_types(df, required_columns)
    errors.extend(col_errors)
    
    # Validate optional columns (if present, check types)
    optional_columns = schema.get("optional_columns", {})
    for col, expected_dtype in optional_columns.items():
        if col in df.columns:
            actual_dtype = str(df[col].dtype)
            if expected_dtype == "string" and not pd.api.types.is_string_dtype(df[col]):
                errors.append(f"Optional column '{col}' expected string type, got {actual_dtype}")
            elif expected_dtype == "integer" and not pd.api.types.is_integer_dtype(df[col]):
                errors.append(f"Optional column '{col}' expected integer type, got {actual_dtype}")
            elif expected_dtype == "float" and not pd.api.types.is_float_dtype(df[col]):
                errors.append(f"Optional column '{col}' expected float type, got {actual_dtype}")
            elif expected_dtype == "boolean" and not pd.api.types.is_bool_dtype(df[col]):
                errors.append(f"Optional column '{col}' expected boolean type, got {actual_dtype}")
            elif expected_dtype == "datetime" and not pd.api.types.is_datetime64_any_dtype(df[col]):
                errors.append(f"Optional column '{col}' expected datetime type, got {actual_dtype}")
    
    # Validate value constraints if defined
    constraints = schema.get("constraints", {})
    for col, constraint in constraints.items():
        if col not in df.columns:
            continue
        
        if "min_value" in constraint:
            if df[col].min() < constraint["min_value"]:
                errors.append(f"Column '{col}' has values below minimum {constraint['min_value']}")
        
        if "max_value" in constraint:
            if df[col].max() > constraint["max_value"]:
                errors.append(f"Column '{col}' has values above maximum {constraint['max_value']}")
        
        if "allowed_values" in constraint:
            invalid_values = set(df[col].unique()) - set(constraint["allowed_values"])
            if invalid_values:
                errors.append(f"Column '{col}' contains invalid values: {invalid_values}")
    
    return len(errors) == 0, errors

def validate_dataset_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate against dataset.schema.yaml."""
    return validate_schema(df, "dataset")

def validate_scored_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate against scored.schema.yaml."""
    return validate_schema(df, "scored")

def validate_output_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validate against output.schema.yaml."""
    return validate_schema(df, "output")

def main():
    """
    Command-line entry point for schema validation.
    Usage: python -m code.utils.schema_validator --schema <name> --file <path>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate data against schema definitions")
    parser.add_argument("--schema", required=True, choices=list(SCHEMAS.keys()),
                      help="Schema to validate against (dataset, scored, output)")
    parser.add_argument("--file", required=True, help="Path to CSV file to validate")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    
    args = parser.parse_args()
    
    try:
        df = pd.read_csv(args.file)
        logger.info(f"Loaded {len(df)} rows from {args.file}")
        
        is_valid, errors = validate_schema(df, args.schema)
        
        if is_valid:
            logger.info(f"✓ Validation PASSED for schema '{args.schema}'")
            return 0
        else:
            logger.error(f"✗ Validation FAILED for schema '{args.schema}'")
            for error in errors:
                logger.error(f"  - {error}")
            return 1
            
    except Exception as e:
        logger.error(f"Error during validation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())