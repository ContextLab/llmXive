"""
tests/contract/test_schemas.py

Contract tests to validate data schemas against definitions.
"""
import pytest
import pandas as pd
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_features_csv_schema_validation():
    """
    Contract test: Verifies that the features.csv file (if it exists) 
    matches the expected schema defined in contracts/data-schema.yaml.
    
    Note: This test assumes the file exists after T018 (preprocess) runs.
    For T012, this test validates the *expectation* of the schema structure.
    """
    schema_path = Path("contracts/data-schema.yaml")
    if not schema_path.exists():
        # If schema doesn't exist, we might skip or create a default expectation
        # For this task, we assume the schema file is created in T006.
        # If T006 is completed, this file should exist.
        pytest.skip("Schema definition file not found. Skipping contract test.")

    # Load schema
    import yaml
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    expected_columns = set(schema.get("columns", {}).keys())
    expected_types = schema.get("columns", {})

    # If we are testing the output of T012 (download), the output is JSON.
    # This test is for the CSV produced by T018. 
    # However, the task list says T011 is a contract test for features.csv.
    # We will check if the file exists and validate.
    
    features_path = Path("data/processed/features.csv")
    if not features_path.exists():
        pytest.skip("features.csv not found. Run preprocessing first.")

    df = pd.read_csv(features_path)

    # Check columns
    missing_cols = expected_columns - set(df.columns)
    assert not missing_cols, f"Missing columns in features.csv: {missing_cols}"

    # Check types (basic check for non-null)
    for col, type_info in expected_types.items():
        if type_info.get("nullable") == False:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Column {col} has {null_count} null values, but schema requires non-null."
    
    logger.info("Contract test passed: features.csv matches schema.")
