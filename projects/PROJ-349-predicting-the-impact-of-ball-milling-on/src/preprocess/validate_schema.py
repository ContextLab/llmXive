"""
T017a: Schema Validation.
"""
import logging
import pandas as pd
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

def load_schema(schema_path: str = "contracts/dataset.schema.yaml") -> dict:
    """Load schema from YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validates dataframe against the schema.
    Raises InsufficientDataError if validation fails.
    """
    schema = load_schema()
    required_fields = schema.get('required_fields', [])
    
    missing_fields = [f for f in required_fields if f not in df.columns]
    
    if missing_fields:
        from src.exceptions import InsufficientDataError
        raise InsufficientDataError(f"Schema validation failed. Missing required fields: {missing_fields}")
    
    logger.info("Schema validation passed.")
    return True
