"""
Feature Extraction Pipeline Wrapper (T018).

Consumes the processed raw data stream (from T009/T013),
extracts linguistic features using code/features.py,
validates the output against the feature_vector schema using Pydantic,
and saves the result to data/processed/features.csv.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import yaml

# Project imports based on API surface
from config import get_paths, init_run
from utils.logging import setup_logging, get_logger
from features import extract_features_batch
from models.linguistic_feature_vector import LinguisticFeatureVector

# Setup logging
logger = get_logger(__name__)

# Constants
SCHEMA_PATH = "specs/001-llmxive-follow-up-extending-lens-rethink/contracts/feature_vector.schema.yaml"
OUTPUT_PATH = "data/processed/features.csv"
INPUT_PATH = "data/processed/sample_stream.jsonl"  # Assumed output from T009/T013 sampling

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the JSON/YAML schema definition for validation."""
    path = Path(schema_path)
    if not path.exists():
        logger.error(f"Schema file not found: {path}")
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any]) -> bool:
    """
    Validate the DataFrame against the Pydantic model and schema.
    Raises ValueError on mismatch.
    """
    if df.empty:
        logger.warning("DataFrame is empty. Validation passed trivially, but check upstream.")
        return True

    required_fields = schema.get('properties', {}).keys()
    if not required_fields:
        logger.warning("Schema has no properties defined. Skipping strict validation.")
        return True

    # Check column presence
    missing_cols = set(required_fields) - set(df.columns)
    if missing_cols:
        error_msg = f"DataFrame missing required columns: {missing_cols}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Check data types and non-null constraints via Pydantic
    # We attempt to parse each row as the Pydantic model to ensure strict validity
    validation_errors = []
    for idx, row in df.iterrows():
        try:
            # Convert row to dict, handling potential NaNs if schema allows nulls or requires coercion
            row_dict = row.to_dict()
            # Pydantic V1/V2 compatibility: parse_obj or model_validate
            if hasattr(LinguisticFeatureVector, 'model_validate'):
                LinguisticFeatureVector.model_validate(row_dict)
            else:
                LinguisticFeatureVector.parse_obj(row_dict)
        except Exception as e:
            validation_errors.append(f"Row {idx}: {str(e)}")
            # Fail loudly on first error as per constraint
            break

    if validation_errors:
        error_msg = f"Pydantic validation failed:\n{validation_errors[0]}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info("DataFrame validation passed against schema and Pydantic model.")
    return True

def main():
    """
    Main entry point for the feature extraction pipeline.
    1. Load input data (processed raw stream).
    2. Extract features.
    3. Validate against schema.
    4. Save to CSV.
    """
    # Initialize project paths and logging
    paths = get_paths()
    setup_logging()

    # Ensure output directory exists
    output_dir = Path(paths.processed_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    input_file = Path(paths.raw_dir) / "sample_stream.jsonl"
    # Fallback to expected T009 output if specific sampling file isn't named yet
    if not input_file.exists():
        input_file = Path(paths.raw_dir) / "pick-a-pic-stream.jsonl"
    
    if not input_file.exists():
        # Check data/processed as per task description "consume processed raw data stream"
        input_file = Path(paths.processed_dir) / "sample_stream.jsonl"
    
    if not input_file.exists():
        logger.error(f"Input data file not found at {input_file}. Ensure T009/T013 completed.")
        sys.exit(1)

    logger.info(f"Loading input data from {input_file}")
    try:
        # Load JSONL into DataFrame
        # Assuming the stream produces a JSONL with 'caption' and potentially 'id'
        df_raw = pd.read_json(input_file, lines=True)
    except Exception as e:
        logger.error(f"Failed to load input data: {e}")
        sys.exit(1)

    if 'caption' not in df_raw.columns:
        logger.error("Input data missing 'caption' column.")
        sys.exit(1)

    logger.info(f"Extracting features for {len(df_raw)} captions...")
    try:
        df_features = extract_features_batch(df_raw['caption'].tolist())
    except Exception as e:
        logger.error(f"Feature extraction failed: {e}")
        sys.exit(1)

    if df_features.empty:
        logger.error("Feature extraction returned empty DataFrame.")
        sys.exit(1)

    # 1. Load Schema
    schema = load_schema(SCHEMA_PATH)

    # 2. Validate DataFrame
    try:
        validate_dataframe(df_features, schema)
    except ValueError as ve:
        logger.critical(f"Validation failed: {ve}")
        sys.exit(1)

    # 3. Save to CSV
    output_file = Path(paths.processed_dir) / "features.csv"
    logger.info(f"Saving validated features to {output_file}")
    df_features.to_csv(output_file, index=False)

    logger.info("Feature extraction pipeline completed successfully.")

if __name__ == "__main__":
    main()