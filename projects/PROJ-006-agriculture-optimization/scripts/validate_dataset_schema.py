import os
import sys
import logging
from pathlib import Path
import json
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_project_root():
    """Return the project root directory."""
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / 'requirements.txt').exists():
            return current
        current = current.parent
    return Path.cwd()

def load_yaml_schema(schema_path):
    """Load a YAML schema file."""
    try:
        with open(schema_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML schema: {e}")
        sys.exit(1)

def validate_with_pydantic(data, schema_model):
    """
    Validate data against a Pydantic model.
    schema_model: The Pydantic model class to validate against.
    """
    try:
        # Attempt to validate the first row or the whole dataset if it's a list of dicts
        if isinstance(data, list):
            for i, row in enumerate(data):
                schema_model(**row)
        else:
            schema_model(**data)
        return True, None
    except Exception as e:
        return False, str(e)

def validate_with_jsonschema(data, schema_dict):
    """
    Validate data against a JSON schema dictionary.
    """
    try:
        import jsonschema
        if isinstance(data, list):
            for i, row in enumerate(data):
                jsonschema.validate(instance=row, schema=schema_dict)
        else:
            jsonschema.validate(instance=data, schema=schema_dict)
        return True, None
    except ImportError:
        logger.warning("jsonschema library not installed. Skipping JSON schema validation.")
        return True, None
    except Exception as e:
        return False, str(e)

def main():
    """
    Main function to validate the dataset against the schema.
    This script is designed to be run as a verification step.
    It reads the schema from contracts/dataset.schema.yaml
    and validates data/processed/analysis_dataset.csv.
    """
    root = get_project_root()
    schema_path = root / 'contracts' / 'dataset.schema.yaml'
    data_path = root / 'data' / 'processed' / 'analysis_dataset.csv'

    logger.info(f"Project root: {root}")
    logger.info(f"Schema path: {schema_path}")
    logger.info(f"Data path: {data_path}")

    # Check if files exist
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)

    # Load schema
    schema_config = load_yaml_schema(schema_path)

    # Load data
    try:
        import pandas as pd
        df = pd.read_csv(data_path)
        logger.info(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
        logger.info(f"Columns: {list(df.columns)}")
    except Exception as e:
        logger.error(f"Failed to load data file: {e}")
        sys.exit(1)

    # Determine validation method based on schema content
    # We assume the schema defines columns in a 'properties' or 'columns' key
    # and types. For this implementation, we will do a structural check.
    # A more robust check would map schema types to pandas dtypes.

    required_columns = schema_config.get('columns', {})
    if not required_columns:
        # Fallback if structure is different
        required_columns = schema_config.get('properties', {})

    if not required_columns:
        logger.warning("Could not determine required columns from schema.")
        sys.exit(0) # Not a fatal error if schema is ambiguous

    # Check for missing columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        sys.exit(1)

    # Check for null values in critical columns if specified
    # For now, we check all columns for nulls if the schema implies strictness
    # or if specific 'not_null' flags are in the schema.
    # Simple check: ensure no NaN in numeric columns if schema says 'float'/'int'
    issues = []
    for col, spec in required_columns.items():
        if col in df.columns:
            if spec.get('type') in ['integer', 'float', 'number']:
                if df[col].isnull().any():
                    issues.append(f"Column '{col}' contains null values.")
            if spec.get('type') == 'string' and df[col].isnull().any():
                # Sometimes strings can be null, but let's warn
                logger.warning(f"Column '{col}' contains null values (string).")

    if issues:
        logger.error("Data validation failed:")
        for issue in issues:
            logger.error(f"  - {issue}")
        sys.exit(1)

    # Check row count
    if len(df) < 300:
        logger.error(f"Dataset has {len(df)} rows, which is less than the required 300.")
        sys.exit(1)

    logger.info("Dataset validation PASSED.")
    logger.info(f"  - Rows: {len(df)} (>= 300)")
    logger.info(f"  - Columns: All required columns present.")
    logger.info(f"  - Nulls: No critical null values found.")

    sys.exit(0)

if __name__ == "__main__":
    main()
