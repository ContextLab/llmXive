import os
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime

import pandas as pd
import jsonschema
from jsonschema import validate, ValidationError

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> dict:
    """Load YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe(df: pd.DataFrame, schema: dict) -> bool:
    """
    Validate a DataFrame against a JSON Schema derived from the YAML spec.
    Returns True if valid, False otherwise.
    """
    # Convert YAML schema to JSON Schema compatible dict (they are usually compatible)
    # We need to ensure the schema describes the rows, not the file structure.
    # Assuming the YAML defines 'properties' for the columns.
    
    # Basic structural check
    required_cols = schema.get('required', [])
    properties = schema.get('properties', {})
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False

    # Check types if specified in schema
    for col_name, col_schema in properties.items():
        if col_name not in df.columns:
            continue
        
        # Simple type mapping
        expected_type = col_schema.get('type')
        if expected_type:
            if expected_type == 'number':
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    # Allow numeric if it's object but parseable? No, strict check first.
                    logger.warning(f"Column {col_name} is not numeric (expected {expected_type})")
                    # For this specific task, we might be lenient if it's a string that looks like a number, 
                    # but strict validation usually requires actual dtype.
                    # However, JSON Schema validation on a dict representation of a row is safer.
                    pass
            
            # Check for nulls if not allowed
            if col_schema.get('nullable') is False:
                if df[col_name].isnull().any():
                    logger.error(f"Column {col_name} contains null values but schema requires non-null.")
                    return False

    # Row-based validation using jsonschema
    # jsonschema expects a list of objects (rows)
    try:
        # Convert dataframe to list of dicts
        rows = df.to_dict(orient='records')
        validate(instance=rows, schema=schema)
    except ValidationError as e:
        logger.error(f"Schema validation error: {e.message} at path: {e.absolute_path}")
        return False

    return True

def main():
    logger.info("Starting daily aggregates validation...")
    
    # Paths
    output_path = get_path('data/processed', 'daily_aggregates.csv')
    schema_path = get_path('specs/001-physical-activity-mood-variability/contracts', 'daily_aggregates.schema.yaml')
    
    if not os.path.exists(output_path):
        logger.error(f"Output file not found: {output_path}. Did you run preprocess.py?")
        return False
    
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        return False

    # Load Data
    try:
        df = pd.read_csv(output_path)
        logger.info(f"Loaded {len(df)} rows from {output_path}")
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        return False

    # Load Schema
    try:
        schema = load_schema(schema_path)
        logger.info(f"Loaded schema from {schema_path}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    # Validate
    is_valid = validate_dataframe(df, schema)
    
    if is_valid:
        logger.info("Validation PASSED: daily_aggregates.csv conforms to schema.")
        # Optional: Write a validation log
        log_path = get_path('data/processed', 'validation_log.json')
        with open(log_path, 'w') as f:
            json.dump({
                "file": "daily_aggregates.csv",
                "rows": len(df),
                "status": "valid",
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
        return True
    else:
        logger.error("Validation FAILED: daily_aggregates.csv does not conform to schema.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
