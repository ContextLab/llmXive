import os
import sys
import logging
from pathlib import Path
import json
import yaml

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.config.schemas import validate_dataset_schema
from src.utils.io_helpers import load_json_strict, write_json_strict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_project_root():
    return project_root

def load_yaml_schema(path: Path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_with_pydantic(df):
    """
    Validates a DataFrame against the Pydantic-based schema defined in src/config/schemas.py.
    Returns (is_valid, errors).
    """
    try:
        is_valid, errors = validate_dataset_schema(df)
        return is_valid, errors
    except Exception as e:
        logger.error(f"Pydantic validation error: {e}")
        return False, [str(e)]

def validate_with_jsonschema(df, schema_dict):
    """
    Validates a DataFrame against a JSON Schema dict.
    Note: This is a placeholder for future JSON Schema integration if needed.
    Currently, we rely on Pydantic for robust validation.
    """
    logger.warning("JSON Schema validation not fully implemented. Using Pydantic fallback.")
    return validate_with_pydantic(df)

def main():
    """
    Main entry point for validating the dataset schema.
    This script is intended for CI/CD pipelines to verify data integrity.
    """
    # Example: Validate the synthetic dataset if it exists
    data_path = project_root / "data" / "processed" / "analysis_dataset.csv"
    schema_path = project_root / "contracts" / "dataset.schema.yaml"

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)

    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)

    import pandas as pd
    df = pd.read_csv(data_path)

    logger.info(f"Validating {data_path}...")
    is_valid, errors = validate_with_pydantic(df)

    if is_valid:
        logger.info("Validation PASSED.")
        sys.exit(0)
    else:
        logger.error("Validation FAILED.")
        for err in errors:
            logger.error(f"  - {err}")
        sys.exit(1)

if __name__ == "__main__":
    main()
