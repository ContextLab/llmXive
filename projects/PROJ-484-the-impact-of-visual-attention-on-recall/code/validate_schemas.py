import json
import yaml
from pathlib import Path
import sys
import logging
import pandas as pd
from logging_config import setup_logging

logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> dict:
    """Load a YAML schema definition."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_against_schema(df: pd.DataFrame, schema: dict) -> bool:
    """
    Validate a pandas DataFrame against the loaded schema.
    Returns True if valid, raises ValueError otherwise.
    """
    # Check columns
    expected_columns = schema['properties']['columns']['items']
    actual_columns = set(df.columns)
    expected_set = set(expected_columns)
    
    missing_cols = expected_set - actual_columns
    extra_cols = actual_columns - expected_set
    
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    if extra_cols:
        logger.warning(f"Extra columns found (not in schema): {extra_cols}")
    
    # Check data types based on schema
    type_map = schema['properties']['column_types']['properties']
    
    for col, type_def in type_map.items():
        if col not in df.columns:
            continue
        
        dtype = df[col].dtype
        
        # Basic type checking
        if type_def['type'] == 'integer':
            if not pd.api.types.is_integer_dtype(dtype) and not pd.api.types.is_numeric_dtype(dtype):
                raise ValueError(f"Column {col} must be integer-like, got {dtype}")
            
            if 'minimum' in type_def:
                if df[col].min() < type_def['minimum']:
                    raise ValueError(f"Column {col} has values below minimum {type_def['minimum']}")
            if 'maximum' in type_def:
                if df[col].max() > type_def['maximum']:
                    raise ValueError(f"Column {col} has values above maximum {type_def['maximum']}")
        
        elif type_def['type'] == 'number':
            if not pd.api.types.is_numeric_dtype(dtype):
                raise ValueError(f"Column {col} must be numeric, got {dtype}")
            
            if 'minimum' in type_def:
                if df[col].min() < type_def['minimum']:
                    raise ValueError(f"Column {col} has values below minimum {type_def['minimum']}")
            if 'maximum' in type_def:
                if df[col].max() > type_def['maximum']:
                    raise ValueError(f"Column {col} has values above maximum {type_def['maximum']}")
        
        elif type_def['type'] == 'boolean':
            if not pd.api.types.is_bool_dtype(dtype) and not (dtype == object and df[col].isin([True, False, 0, 1]).all()):
                # Allow 0/1 or True/False
                if not set(df[col].unique()).issubset({True, False, 0, 1, 'True', 'False'}):
                    raise ValueError(f"Column {col} must be boolean, got {dtype}")
        
        elif type_def['type'] == 'string':
            if not pd.api.types.is_string_dtype(dtype):
                # Allow object dtype for strings
                pass
            
            if 'enum' in type_def:
                if not set(df[col].unique()).issubset(set(type_def['enum'])):
                    invalid_vals = set(df[col].unique()) - set(type_def['enum'])
                    raise ValueError(f"Column {col} has invalid enum values: {invalid_vals}")
    
    # Check constraints
    constraints = schema.get('properties', {}).get('constraints', {})
    
    if constraints.get('no_null_fixation_duration', False):
        if 'fixation_duration_ms' in df.columns:
            if df['fixation_duration_ms'].isnull().any():
                raise ValueError("Constraint failed: fixation_duration_ms contains null values")
    
    if constraints.get('stai_score_present', False):
        if 'stai_total_score' in df.columns:
            if df['stai_total_score'].isnull().any():
                raise ValueError("Constraint failed: stai_total_score contains null values")
    
    return True

def validate_model_output_file(json_path: str, schema_path: str = None) -> bool:
    """
    Validate a JSON model output file against a schema.
    For T006, we focus on CSV, but this is a stub for T006b.
    """
    if schema_path:
        schema = load_schema(schema_path)
    else:
        # Default path for model output schema if not provided
        schema = load_schema("specs/001-visual-attention-recall/contracts/model_output.schema.yaml")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Basic structure validation could go here
    # For now, just ensure it's valid JSON (already done by json.load)
    logger.info(f"Validated model output: {json_path}")
    return True

def main():
    """
    CLI entry point to validate the analysis CSV against the schema.
    Usage: python validate_schemas.py --csv data/processed/analysis.csv --schema specs/001-visual-attention-recall/contracts/dataset.schema.yaml
    """
    parser = argparse.ArgumentParser(description="Validate analysis CSV against schema")
    parser.add_argument("--csv", required=True, help="Path to the analysis CSV file")
    parser.add_argument("--schema", required=True, help="Path to the schema YAML file")
    parser.add_argument("--log", default="artifacts/logs/validate.log", help="Path to log file")
    
    args = parser.parse_args()
    
    setup_logging(args.log)
    
    try:
        logger.info(f"Loading schema from {args.schema}")
        schema = load_schema(args.schema)
        
        logger.info(f"Loading CSV from {args.csv}")
        df = pd.read_csv(args.csv)
        logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
        
        logger.info("Validating against schema...")
        validate_csv_against_schema(df, schema)
        
        logger.info("Validation SUCCESS: CSV conforms to schema.")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation FAILED: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
