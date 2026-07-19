"""
Schema validator for dataset CSV files.

Validates CSV structure against contracts/dataset.schema.yaml
"""
import os
import sys
import csv
import yaml
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Import from project structure
from config import get_project_root, get_logs_dir, ensure_directories
from utils.logger import setup_logging

def setup_logger(log_file: Optional[str] = None):
    """Setup logging for the validator."""
    if log_file is None:
        log_dir = get_logs_dir()
        ensure_directories()
        log_file = os.path.join(log_dir, 'validation.log')
    setup_logging(log_file)
    return logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load schema from YAML file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Schema dictionary.
        
    Raises:
        FileNotFoundError: If schema file not found.
        yaml.YAMLError: If schema file is invalid YAML.
    """
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    return schema

def validate_csv_schema(df: Any, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Validate CSV DataFrame against schema.
    
    Args:
        df: pandas DataFrame to validate.
        schema_path: Path to schema YAML file.
        
    Returns:
        Tuple of (is_valid, list of error messages).
    """
    logger = setup_logger()
    errors = []
    
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        errors.append(f"Failed to load schema: {str(e)}")
        return False, errors
    
    required_cols = schema.get('required_columns', [])
    optional_cols = schema.get('optional_columns', [])
    all_schema_cols = required_cols + optional_cols
    schema_col_names = [col['name'] for col in all_schema_cols]
    
    df_columns = set(df.columns)
    
    # Check required columns
    missing_required = []
    for col_def in required_cols:
        col_name = col_def['name']
        if col_name not in df_columns:
            missing_required.append(col_name)
    
    if missing_required:
        errors.append(f"Missing required columns: {missing_required}")
        logger.error(f"Missing required columns: {missing_required}")
    
    # Check for unknown columns (optional warning)
    unknown_cols = df_columns - set(schema_col_names)
    if unknown_cols:
        logger.warning(f"Found columns not in schema: {unknown_cols}")
        # We allow unknown columns for now, just warn
    
    # Validate data types for required columns
    for col_def in required_cols:
        col_name = col_def['name']
        if col_name in df_columns:
            col_type = col_def.get('type', 'numeric')
            if col_type == 'numeric':
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    errors.append(f"Column '{col_name}' is not numeric as expected")
                    logger.error(f"Column '{col_name}' is not numeric")
    
    is_valid = len(errors) == 0
    if is_valid:
        logger.info("Schema validation passed.")
    else:
        logger.error(f"Schema validation failed with {len(errors)} errors.")
    
    return is_valid, errors

def validate_and_report(csv_path: str, schema_path: str) -> bool:
    """
    Validate a CSV file against schema and report results.
    
    Args:
        csv_path: Path to CSV file.
        schema_path: Path to schema YAML file.
        
    Returns:
        True if validation passes, False otherwise.
    """
    import pandas as pd
    
    logger = setup_logger()
    
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return False
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {str(e)}")
        return False
    
    is_valid, errors = validate_csv_schema(df, schema_path)
    
    if not is_valid:
        for err in errors:
            logger.error(err)
    
    return is_valid

def main():
    """
    CLI entry point for schema validation.
    """
    import argparse
    import pandas as pd
    
    parser = argparse.ArgumentParser(description='Validate CSV against schema')
    parser.add_argument('--csv', required=True, help='Path to CSV file')
    parser.add_argument('--schema', required=True, help='Path to schema YAML')
    args = parser.parse_args()
    
    ensure_directories()
    
    success = validate_and_report(args.csv, args.schema)
    
    if not success:
        sys.exit(1)
    else:
        print("Validation successful.")
        sys.exit(0)

if __name__ == "__main__":
    main()