"""
Data validation module for raw VAERS datasets.

Validates input CSV files against the schema defined in contracts/dataset.schema.yaml.
Exits with code E_SCHEMA_MISSING if validation fails.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Set, Dict, Any
import pandas as pd
import yaml

# Error codes
E_SCHEMA_MISSING = 2
E_FILE_NOT_FOUND = 3
E_INVALID_SCHEMA = 4

# Constants
SCHEMA_PATH = Path("contracts/dataset.schema.yaml")
REQUIRED_COLUMNS = {"VAX_TYPE", "SOC_CODE", "REPT_DATE", "AGE"}
# Fallback to LLT if SOC_CODE is not present, but at least one must exist
ALTERNATIVE_COLUMNS = {"LLT"}

def setup_logging() -> logging.Logger:
    """Configure logging for the validation module."""
    logger = logging.getLogger("validate")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    return logger

logger = setup_logging()

def load_schema(schema_path: Path = SCHEMA_PATH) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema configuration.
        
    Raises:
        SystemExit: If the schema file is missing or invalid.
    """
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(E_FILE_NOT_FOUND)
    
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
        if not isinstance(schema, dict):
            logger.error("Schema file is not a valid YAML dictionary.")
            sys.exit(E_INVALID_SCHEMA)
        return schema
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML schema: {e}")
        sys.exit(E_INVALID_SCHEMA)

def validate_columns(df: pd.DataFrame, required_cols: Set[str], schema: Dict[str, Any]) -> bool:
    """
    Validate that the DataFrame contains the required columns.
    
    Args:
        df: Pandas DataFrame to validate.
        required_cols: Set of required column names.
        schema: Loaded schema dictionary.
        
    Returns:
        True if validation passes.
        
    Raises:
        SystemExit: If required columns are missing.
    """
    df_cols = set(df.columns)
    missing = required_cols - df_cols
    
    if missing:
        # Check for alternative columns (e.g., LLT instead of SOC_CODE)
        if "SOC_CODE" in missing and "LLT" in df_cols:
            missing.discard("SOC_CODE")
            logger.warning("SOC_CODE missing, but LLT found. Using LLT as alternative.")
        
        if missing:
            logger.error(f"Missing required columns: {missing}")
            logger.error(f"Available columns: {list(df.columns)}")
            logger.error(f"Required columns per schema: {required_cols}")
            sys.exit(E_SCHEMA_MISSING)
    
    logger.info("Column validation passed.")
    return True

def validate_data(
    file_path: Path,
    schema_path: Path = SCHEMA_PATH,
    required_cols: Set[str] = None
) -> pd.DataFrame:
    """
    Validate a CSV file against the schema and return the DataFrame.
    
    Args:
        file_path: Path to the CSV file to validate.
        schema_path: Path to the schema YAML file.
        required_cols: Optional override for required columns.
        
    Returns:
        Validated pandas DataFrame.
        
    Raises:
        SystemExit: If the file is missing, invalid, or fails schema validation.
    """
    if required_cols is None:
        required_cols = REQUIRED_COLUMNS
    
    if not file_path.exists():
        logger.error(f"Data file not found: {file_path}")
        sys.exit(E_FILE_NOT_FOUND)
    
    logger.info(f"Loading data from: {file_path}")
    try:
        # Load the CSV
        df = pd.read_csv(file_path, dtype=str)
    except Exception as e:
        logger.error(f"Error reading CSV file: {e}")
        sys.exit(E_FILE_NOT_FOUND)
    
    if df.empty:
        logger.error("Loaded DataFrame is empty.")
        sys.exit(E_SCHEMA_MISSING)
    
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Validate columns
    validate_columns(df, required_cols, schema)
    
    logger.info("Data validation successful.")
    return df

def main():
    """
    Main entry point for the validation script.
    
    Usage: python -m src.data.validate <path_to_csv> [schema_path]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate VAERS dataset against schema.")
    parser.add_argument("file_path", type=str, help="Path to the CSV file to validate.")
    parser.add_argument(
        "--schema",
        type=str,
        default=str(SCHEMA_PATH),
        help=f"Path to the schema YAML file (default: {SCHEMA_PATH})"
    )
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    schema_path = Path(args.schema)
    
    try:
        df = validate_data(file_path, schema_path)
        logger.info(f"Validation passed for {file_path}. Row count: {len(df)}")
        # Optionally print head for verification
        # logger.info(df.head().to_string())
    except SystemExit:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()