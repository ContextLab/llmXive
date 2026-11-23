"""
Module to save and validate daily aggregates.
This script is the final writer for data/processed/daily_aggregates.csv.
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import yaml
from config import get_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_schema(schema_path):
    """Load a YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe(df, schema):
    """
    Validate a DataFrame against a YAML schema.
    Returns (is_valid, errors_list)
    """
    errors = []
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    # Check required columns
    for field in required_fields:
        if field not in df.columns:
            errors.append(f"Missing required column: {field}")

    # Check types and constraints
    for col_name, col_schema in properties.items():
        if col_name not in df.columns:
            continue
        
        col_data = df[col_name]
        
        # Type checks
        if 'type' in col_schema:
            expected_type = col_schema['type']
            if expected_type == 'integer':
                if not pd.api.types.is_integer_dtype(col_data) and not pd.api.types.is_numeric_dtype(col_data):
                    # Allow numeric if it's effectively integer
                    if not col_data.apply(lambda x: float(x).is_integer()).all():
                        errors.append(f"Column {col_name} should be integer type")
            elif expected_type == 'float':
                if not pd.api.types.is_float_dtype(col_data) and not pd.api.types.is_numeric_dtype(col_data):
                    errors.append(f"Column {col_name} should be float type")
            elif expected_type == 'string':
                if not pd.api.types.is_string_dtype(col_data) and not pd.api.types.is_object_dtype(col_data):
                    errors.append(f"Column {col_name} should be string type")
            elif expected_type == 'date':
                # Check if it can be parsed as date
                try:
                    pd.to_datetime(col_data)
                except (ValueError, TypeError):
                    errors.append(f"Column {col_name} should be date type")

        # Min/Max constraints
        if 'min' in col_schema:
            if col_data.min() < col_schema['min']:
                errors.append(f"Column {col_name} has values below minimum {col_schema['min']}")
        
        if col_schema.get('nullable') is False:
            if col_data.isna().any():
                errors.append(f"Column {col_name} contains null values but is not nullable")

    return len(errors) == 0, errors

def save_and_validate(df, output_path, schema_path):
    """
    Save DataFrame to CSV and validate against schema.
    Raises RuntimeError if validation fails.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Validate against schema
    schema = load_schema(schema_path)
    is_valid, errors = validate_dataframe(df, schema)
    
    if not is_valid:
        error_msg = "Schema validation failed:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Specific task T015 constraint: Assert no NaN/Inf in mood_std
    if 'mood_std' in df.columns:
        assert (df['mood_std'] >= 0).all(), "mood_std contains negative values"
        assert np.isfinite(df['mood_std']).all(), "mood_std contains NaN or Inf values"
        logger.info(f"mood_std validation passed: min={df['mood_std'].min():.4f}, max={df['mood_std'].max():.4f}")

    # Write to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Successfully saved {len(df)} rows to {output_path}")
    return True

def main():
    """Main entry point for saving daily aggregates."""
    logger.info("Starting save_daily_aggregates script")
    
    # Define paths
    input_path = get_path("data", "processed", "daily_aggregates.csv")
    schema_path = get_path("specs", "001-physical-activity-levels-and-mood-variab", "contracts", "daily_aggregates.schema.yaml")
    output_path = get_path("data", "processed", "daily_aggregates.csv")
    
    # Check if input exists (it should be produced by preprocess.py)
    if not os.path.exists(input_path):
        # If the file doesn't exist, we assume the previous step (preprocess) 
        # failed or didn't run. We cannot fabricate data.
        raise FileNotFoundError(f"Input file not found at {input_path}. Run preprocess.py first.")
    
    # Load the data
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {input_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to load input file: {e}")
    
    # Save and validate
    try:
        save_and_validate(df, output_path, schema_path)
    except RuntimeError as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
    
    logger.info("Save and validation completed successfully")

if __name__ == "__main__":
    main()