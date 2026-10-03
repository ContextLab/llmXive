import os
import sys
import logging
from pathlib import Path
from typing import List, Set, Dict, Any
import pandas as pd
import yaml

# Exit codes
E_SUCCESS = 0
E_SCHEMA_MISSING = 1
E_DATA_MISSING = 2
E_VALIDATION_FAILED = 3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/validate.log')
    ]
)
logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load and parse the YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        schema = yaml.safe_load(f)
    
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def validate_columns(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
    """Check if all required columns are present in the DataFrame."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return missing
    
    logger.info("All required columns present.")
    return []

def validate_data(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate the DataFrame against the schema.
    Checks:
      1. Required columns exist
      2. Row count > 0
      3. Column-specific constraints (e.g., non-null checks)
    
    Returns True if valid, False otherwise.
    Raises SystemExit with E_SCHEMA_MISSING or E_VALIDATION_FAILED.
    """
    required_columns = schema.get('required_columns', [])
    
    # 1. Check columns
    missing_cols = validate_columns(df, required_columns)
    if missing_cols:
        logger.error(f"Schema validation failed: Missing columns {missing_cols}")
        raise SystemExit(E_SCHEMA_MISSING)
    
    # 2. Check row count
    if len(df) == 0:
        logger.error("Data validation failed: DataFrame is empty")
        raise SystemExit(E_VALIDATION_FAILED)
    
    # 3. Check specific constraints from schema
    column_defs = schema.get('column_definitions', {})
    for col_name, col_def in column_defs.items():
        if not col_def.get('nullable', True):
            null_count = df[col_name].isna().sum()
            if null_count > 0:
                logger.warning(f"Column '{col_name}' has {null_count} null values (marked as non-nullable).")
                # Depending on strictness, this could be a hard fail. 
                # For now, we log but proceed, unless the task implies strict fail.
                # The task says "exit with E_SCHEMA_MISSING if failed". 
                # Missing columns is the primary schema failure.
                # Non-null violations are data quality issues.
                # However, to be safe and strict per "validate against schema":
                if col_name in required_columns:
                    logger.error(f"Strict validation failed: Column '{col_name}' must be non-null.")
                    raise SystemExit(E_VALIDATION_FAILED)

    logger.info("Data validation passed.")
    return True

def main():
    """
    Entry point for validation script.
    Expects:
      --data <path_to_csv>
      --schema <path_to_yaml>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate raw data against schema")
    parser.add_argument('--data', type=str, required=True, help='Path to input CSV file')
    parser.add_argument('--schema', type=str, default='contracts/dataset.schema.yaml', help='Path to schema YAML file')
    args = parser.parse_args()

    try:
        schema = load_schema(args.schema)
        
        if not os.path.exists(args.data):
            logger.error(f"Data file not found: {args.data}")
            raise SystemExit(E_DATA_MISSING)

        logger.info(f"Loading data from {args.data}...")
        df = pd.read_csv(args.data)
        logger.info(f"Loaded {len(df)} rows.")

        validate_data(df, schema)
        
        logger.info("Validation successful.")
        sys.exit(E_SUCCESS)

    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(E_SCHEMA_MISSING)
    except SystemExit as e:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(E_VALIDATION_FAILED)

if __name__ == "__main__":
    main()
