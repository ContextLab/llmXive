"""
Integration test for the full ingestion pipeline (User Story 1).

This test validates the entire data ingestion flow:
1. Fetches real data from configured sources.
2. Cleans and processes the data.
3. Engineers features (ratios, interactions, orthogonalization).
4. Validates the final output DataFrame against the schema defined in
   `contracts/dataset.schema.yaml`.

It ensures no null values exist in the target variable and that all
required columns are present with correct types.
"""

import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path

import pytest
import pandas as pd
import numpy as np
import yaml

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.ingest import run_ingestion
from src.data.features import engineer_features
from src.utils.config import DATA_RAW_DIR, DATA_PROCESSED_DIR, PROJECT_ROOT as CFG_ROOT

# Configure logging for the test run
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants for validation
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "dataset.schema.yaml"

# Required columns based on typical steel yield strength prediction requirements
# (Composition, Thermal Params, Derived Interactions, Orthogonalized Interactions)
# These will be dynamically checked against the schema if available, or asserted here.
REQUIRED_TARGET_COLUMN = "yield_strength_mpa"

def load_schema(schema_path: Path) -> dict:
    """Load and parse the dataset schema YAML."""
    if not schema_path.exists():
        pytest.fail(f"Schema file not found at {schema_path}. Ensure contracts/dataset.schema.yaml exists.")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_dataframe_schema(df: pd.DataFrame, schema: dict) -> None:
    """
    Validate the DataFrame against the loaded schema.

    Checks:
    - All required columns exist.
    - Column types match (if specified).
    - No null values in the target variable.
    """
    required_columns = schema.get("required_columns", [])
    target_column = schema.get("target_column")

    # Check for required columns
    missing_columns = set(required_columns) - set(df.columns)
    if missing_columns:
        pytest.fail(f"Missing required columns: {missing_columns}")

    # Check target column nulls
    if target_column and target_column in df.columns:
        if df[target_column].isnull().any():
            pytest.fail(f"Target column '{target_column}' contains null values.")

    # Type checks (basic)
    for col_name, col_type in schema.get("column_types", {}).items():
        if col_name in df.columns:
            if col_type == "numeric":
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    pytest.fail(f"Column '{col_name}' must be numeric.")
            elif col_type == "string":
                if not pd.api.types.is_string_dtype(df[col_name]):
                    pytest.fail(f"Column '{col_name}' must be string.")

@pytest.mark.integration
def test_full_ingestion_pipeline():
    """
    Run the full ingestion pipeline and validate the output.

    This test:
    1. Ensures data directories exist.
    2. Runs `run_ingestion` which fetches, cleans, and saves raw data.
    3. Loads the processed data (or runs feature engineering if part of the pipeline).
       Note: Based on task T013/T014, feature engineering might be a separate step.
       However, T010 is an integration test for the "full ingestion pipeline".
       If `run_ingestion` only does fetch/clean, we must also test the feature
       engineering step here to satisfy "full ingestion pipeline" validation
       against the final schema which includes interactions.
    4. Validates the final DataFrame against the schema.
    """
    # Ensure directories exist
    os.makedirs(DATA_RAW_DIR, exist_ok=True)
    os.makedirs(DATA_PROCESSED_DIR, exist_ok=True)

    # Load schema
    schema = load_schema(SCHEMA_PATH)

    # Step 1: Run Ingestion (Fetch + Clean)
    # This function is expected to download real data and save to data/raw/
    logger.info("Running data ingestion...")
    
    # We assume run_ingestion returns the raw dataframe or saves it and returns path
    # Based on API surface: run_ingestion is the entry point.
    # If it returns a path, we load it. If it returns a DF, we use it.
    # Let's assume it saves to data/raw/ingested.csv or similar and returns the path/df.
    # To be robust, we check the return value.
    
    try:
        raw_df = run_ingestion()
    except Exception as e:
        # If the pipeline fails (e.g., network), we cannot proceed with integration test
        # unless we have a local fallback. Per constraints, we must use real data.
        # If real data fetch fails, the test fails loudly.
        pytest.fail(f"Ingestion pipeline failed to fetch real data: {e}")

    if isinstance(raw_df, str):
        # If it returned a path, load it
        raw_df = pd.read_csv(raw_df)
    
    assert raw_df is not None and not raw_df.empty, "Raw dataframe is empty or None."

    # Step 2: Feature Engineering (Ratios, Interactions, Orthogonalization)
    # The schema likely expects these derived columns.
    logger.info("Running feature engineering...")
    
    # We need to ensure the input to engineer_features has the necessary base columns.
    # Assuming 'run_ingestion' produces a DF with composition and thermal params.
    
    try:
        processed_df = engineer_features(raw_df)
    except Exception as e:
        pytest.fail(f"Feature engineering failed: {e}")

    assert processed_df is not None and not processed_df.empty, "Processed dataframe is empty or None."

    # Step 3: Validation against Schema
    logger.info("Validating processed DataFrame against schema...")
    validate_dataframe_schema(processed_df, schema)

    # Step 4: Specific checks for User Story 1 requirements
    # - No null values in target
    target_col = schema.get("target_column", REQUIRED_TARGET_COLUMN)
    if target_col in processed_df.columns:
        assert processed_df[target_col].notnull().all(), f"Target column '{target_col}' has nulls."
    
    # - Verify interaction columns exist if specified in schema
    interaction_cols = schema.get("interaction_columns", [])
    if interaction_cols:
        for col in interaction_cols:
            assert col in processed_df.columns, f"Interaction column '{col}' missing."

    logger.info("Integration test passed: Pipeline executed and validated successfully.")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
