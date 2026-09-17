"""
Feature Extraction Pipeline Wrapper (T018b).

Consumes the processed raw data stream (from T009),
extracts linguistic features using code/features.py,
calls T018a (code/utils/validation.py) for schema validation,
and saves the result to data/processed/features.csv.

This script is the entry point for US1 feature extraction.
"""
import os
import sys
import logging
from pathlib import Path

# Project imports based on API surface
from config import get_paths, init_run
from utils.logging import setup_logging, get_logger
from features import extract_features_batch
from utils.validation import validate_feature_vector_schema, load_schema

# Setup logging
logger = get_logger(__name__)

# Constants
# The task specifies consuming the "processed raw data stream" from T009.
# T009 materializes to data/raw/pick-a-pic.parquet or similar.
# However, the previous file assumed a JSONL stream.
# We must robustly locate the output of T009.
# T009 description: "materialize the full pick-a-pic dataset to data/raw/pick-a-pic.parquet"
# We will attempt to load the parquet file directly as it is the primary artifact.
INPUT_PARQUET = "data/raw/pick-a-pic.parquet"
OUTPUT_CSV = "data/processed/features.csv"
SCHEMA_PATH = "specs/001-llmxive-follow-up-extending-lens-rethink/contracts/feature_vector.schema.yaml"

def main():
    """
    Main entry point for the feature extraction pipeline (T018b).
    1. Load input data (raw parquet from T009).
    2. Extract features.
    3. Call T018a (validate_feature_vector_schema) for schema validation.
    4. Save to data/processed/features.csv.
    """
    # Initialize project paths and logging
    paths = get_paths()
    setup_logging()

    # Ensure output directory exists
    output_dir = Path(paths.processed_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine input file
    input_file = Path(paths.raw_dir) / "pick-a-pic.parquet"
    
    if not input_file.exists():
        # Fallback to other potential locations if T009 named it differently
        possible_inputs = [
            Path(paths.raw_dir) / "pick-a-pic-stream.jsonl",
            Path(paths.raw_dir) / "sample_stream.jsonl",
            Path(paths.processed_dir) / "sample_stream.jsonl",
        ]
        for p in possible_inputs:
            if p.exists():
                input_file = p
                break

    if not input_file.exists():
        logger.critical(f"Input data file not found at {input_file} or fallbacks. Ensure T009 completed.")
        sys.exit(1)

    logger.info(f"Loading input data from {input_file}")
    
    try:
        import pandas as pd
        if input_file.suffix == '.parquet':
            df_raw = pd.read_parquet(input_file)
        else:
            # Assume JSONL
            df_raw = pd.read_json(input_file, lines=True)
    except Exception as e:
        logger.critical(f"Failed to load input data: {e}")
        sys.exit(1)

    if df_raw.empty:
        logger.critical("Input data is empty.")
        sys.exit(1)

    if 'caption' not in df_raw.columns:
        logger.critical("Input data missing 'caption' column.")
        sys.exit(1)

    logger.info(f"Extracting features for {len(df_raw)} captions...")
    try:
        df_features = extract_features_batch(df_raw['caption'].tolist())
    except Exception as e:
        logger.critical(f"Feature extraction failed: {e}")
        sys.exit(1)

    if df_features.empty:
        logger.critical("Feature extraction returned empty DataFrame.")
        sys.exit(1)

    # 1. Load Schema (T018a dependency)
    try:
        schema = load_schema(SCHEMA_PATH)
    except FileNotFoundError as e:
        logger.critical(f"Schema file not found: {e}")
        sys.exit(1)

    # 2. Call T018a: Validate DataFrame against schema
    # The function validate_feature_vector_schema is expected to raise ValueError on failure
    try:
        validate_feature_vector_schema(df_features, schema)
    except ValueError as ve:
        logger.critical(f"Schema validation (T018a) failed: {ve}")
        sys.exit(1)

    # 3. Save to CSV
    output_file = Path(paths.processed_dir) / "features.csv"
    logger.info(f"Saving validated features to {output_file}")
    df_features.to_csv(output_file, index=False)

    logger.info("Feature extraction pipeline (T018b) completed successfully.")

if __name__ == "__main__":
    main()