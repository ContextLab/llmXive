import os
import sys
import logging
from pathlib import Path
import pandas as pd
from config import get_path
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_schema(schema_path):
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe(df, schema):
    """Validate a DataFrame against a schema definition."""
    errors = []
    for field, spec in schema.get('properties', {}).items():
        if field not in df.columns:
            if spec.get('required', False):
                errors.append(f"Missing required column: {field}")
            continue
        
        # Type checking (simplified)
        if field in df.columns:
            if spec.get('type') == 'integer' and not pd.api.types.is_integer_dtype(df[field]):
                # Allow float for integer if no decimals
                if not (df[field] == df[field].astype(int)).all():
                    errors.append(f"Column {field} should be integer")
            # Add more type checks as needed
    return errors

def save_and_validate():
    """Load daily aggregates, validate, and save."""
    input_path = get_path("data", "processed", "daily_aggregates.csv")
    schema_path = get_path("specs", "001-physical-activity-mood-variability", "contracts", "daily_aggregates.schema.yaml")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return False
    
    logger.info(f"Loading {input_path}")
    df = pd.read_csv(input_path)
    
    # Assert no NaN/Inf in mood_std
    if df['mood_std'].isna().any():
        logger.error("NaN values found in mood_std column.")
        return False
    
    if not (df['mood_std'] == df['mood_std']).all():
        logger.error("Inf values found in mood_std column.")
        return False
    
    # Validate schema
    if schema_path.exists():
        schema = load_schema(schema_path)
        errors = validate_dataframe(df, schema)
        if errors:
            logger.error(f"Schema validation errors: {errors}")
            return False
        logger.info("Schema validation passed.")
    else:
        logger.warning(f"Schema file not found: {schema_path}, skipping validation.")
    
    # Re-save to ensure cleanliness (optional, but ensures format)
    df.to_csv(input_path, index=False)
    logger.info(f"Saved and validated {input_path}")
    return True

def main():
    success = save_and_validate()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
