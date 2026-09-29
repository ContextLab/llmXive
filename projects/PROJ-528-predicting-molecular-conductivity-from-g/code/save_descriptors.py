import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
import yaml
from typing import List, Optional

# Import existing utilities from the project
from code.logging_config import setup_logging
from code.config import RAW_DATA_PATH, TARGET_VAR

# Configure logging
logger = setup_logging()

def load_schema(schema_path: str) -> dict:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_descriptors_schema(df: pd.DataFrame, schema: dict) -> List[str]:
    """
    Validate that the DataFrame contains all columns defined in the schema.
    Returns a list of missing column names.
    """
    expected_fields = schema.get('fields', [])
    missing = [col for col in expected_fields if col not in df.columns]
    return missing

def main():
    """
    Main entry point for T019b: Write Full Descriptors (Base).
    1. Load data/processed/descriptors_base.csv (output of T019a).
    2. Verify against contracts/descriptor_schema.yaml.
    3. Write to data/processed/descriptors.csv.
    4. Verify file existence and non-empty content.
    """
    # Paths
    base_path = 'data/processed/descriptors_base.csv'
    output_path = 'data/processed/descriptors.csv'
    schema_path = 'contracts/descriptor_schema.yaml'

    # Check if base file exists
    if not os.path.exists(base_path):
        logger.error(f"Base descriptors file not found: {base_path}")
        logger.error("T019a must be completed before running T019b.")
        sys.exit(1)

    # Load base descriptors
    logger.info(f"Loading base descriptors from {base_path}")
    try:
        df_base = pd.read_csv(base_path)
    except Exception as e:
        logger.error(f"Failed to load {base_path}: {e}")
        sys.exit(1)

    if df_base.empty:
        logger.error("Base descriptors file is empty.")
        sys.exit(1)

    # Load schema
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        sys.exit(1)

    logger.info(f"Loading schema from {schema_path}")
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        sys.exit(1)

    # Validate schema
    missing_cols = validate_descriptors_schema(df_base, schema)
    if missing_cols:
        logger.error(f"Schema mismatch: missing columns {missing_cols}")
        logger.error("T019a did not produce all required columns.")
        sys.exit(1)

    logger.info("Schema validation passed.")

    # Ensure output directory exists
    os.makedirs('data/processed', exist_ok=True)

    # Write full descriptors
    logger.info(f"Writing full descriptors to {output_path}")
    try:
        df_base.to_csv(output_path, index=False)
    except Exception as e:
        logger.error(f"Failed to write {output_path}: {e}")
        sys.exit(1)

    # Verify write
    if not os.path.exists(output_path):
        logger.error(f"File write verification failed: {output_path} does not exist.")
        sys.exit(1)

    df_verify = pd.read_csv(output_path)
    if df_verify.empty:
        logger.error("File write verification failed: output file is empty.")
        sys.exit(1)

    logger.info(f"T019b: Full descriptors written and verified successfully ({len(df_verify)} rows).")
    sys.exit(0)

if __name__ == '__main__':
    main()