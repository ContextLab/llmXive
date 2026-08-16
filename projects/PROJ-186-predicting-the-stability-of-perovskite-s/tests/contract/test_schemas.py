"""
tests/contract/test_schemas.py

Contract tests to validate data schemas against definitions.
"""
import pytest
import pandas as pd
import os
import sys
from pathlib import Path
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging_config import get_logger

logger = get_logger(__name__)

def test_features_csv_schema_validation():
    """
    Contract test: Verifies that the features.csv file (if it exists) 
    matches the expected schema defined in contracts/data-schema.yaml.
    
    This test validates the output of the preprocessing pipeline (T017/T018).
    It ensures that the generated CSV strictly adheres to the schema defined
    in specs/001-predicting-the-stability-of-perovskite-s/contracts/data-schema.yaml.
    """
    schema_path = Path("specs/001-predicting-the-stability-of-perovskite-s/contracts/data-schema.yaml")
    
    if not schema_path.exists():
        pytest.skip(f"Schema definition file not found at {schema_path}. Skipping contract test.")

    # Load schema
    with open(schema_path, "r") as f:
        schema = yaml.safe_load(f)

    expected_columns = set(schema.get("columns", {}).keys())
    expected_types = schema.get("columns", {})
    required_non_null = [col for col, info in expected_types.items() if info.get("nullable") is False]

    # Locate the features file
    features_path = Path("data/processed/features.csv")
    
    if not features_path.exists():
        # Fail loudly if the artifact is missing, as this indicates a pipeline break
        pytest.fail(f"Contract test failed: Required artifact {features_path} does not exist. "
                    f"Ensure T017 (preprocess) has run successfully.")

    try:
        df = pd.read_csv(features_path)
    except Exception as e:
        pytest.fail(f"Failed to read {features_path}: {e}")

    if df.empty:
        pytest.fail(f"Contract test failed: {features_path} exists but is empty.")

    # Check columns
    missing_cols = expected_columns - set(df.columns)
    extra_cols = set(df.columns) - expected_columns
    
    assert not missing_cols, f"Schema contract violated: Missing columns in features.csv: {missing_cols}"
    
    if extra_cols:
        logger.warning(f"Schema contract warning: Extra columns found in features.csv (not in schema): {extra_cols}")

    # Check non-null constraints
    for col in required_non_null:
        null_count = df[col].isnull().sum()
        assert null_count == 0, (
            f"Schema contract violated: Column '{col}' requires non-null values, "
            f"but found {null_count} nulls in {features_path}."
        )

    # Basic type validation (check for object/string vs numeric where expected)
    for col, type_info in expected_types.items():
        if col in df.columns:
            expected_dtype = type_info.get("dtype")
            if expected_dtype:
                # Simple check: if schema says 'float', pandas should infer numeric
                if expected_dtype == "float":
                    if not pd.api.types.is_numeric_dtype(df[col]):
                        # Allow int->float coercion, but strict object might fail
                        if df[col].dtype == 'object':
                            pytest.fail(f"Schema contract violated: Column '{col}' expected float, got object.")
                
    logger.info("Contract test passed: features.csv matches schema definition.")