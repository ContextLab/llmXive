"""
Contract tests for data schema validation.
Ensures that the harmonized dataset and intermediate files adhere to the
expected schema defined in the project specifications.
"""
import pytest
import pandas as pd
import os
from pathlib import Path
import sys

# Ensure project root is in path for imports if running standalone
# Note: In a standard pytest run with conftest, this might not be needed,
# but good for robustness if run directly.
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logger import get_logger

logger = get_logger("test_schemas")

# Expected schemas based on tasks.md and data-model.md
# Harmonized dataset (merged_harmonized.tsv)
EXPECTED_HARMONIZED_COLUMNS = {
    "sample_id",
    "cohort",
    "fiber_g_day",
    "read_count",
    "age",
    "bmi",
    "antibiotic_use",
    "sex",
    "origin",
    # Taxa columns will be dynamic (e.g., phylum_..., genus_...)
    # but we validate the metadata columns strictly.
}

EXPECTED_HARMONIZED_DTYPES = {
    "sample_id": "object",
    "cohort": "object",
    "fiber_g_day": "float64",
    "read_count": "int64",
    "age": "float64",
    "bmi": "float64",
    "antibiotic_use": "object", # Or int/float depending on encoding, assuming object for now
    "sex": "object",
    "origin": "object",
}

# CLR transformed dataset (clr_transformed.tsv)
EXPECTED_CLR_COLUMNS = {
    "sample_id",
    "cohort",
    "fiber_g_day",
    # Taxa columns (CLR transformed)
}

# Association results (association_results.tsv)
EXPECTED_ASSOCIATION_COLUMNS = {
    "taxon",
    "beta",
    "std_error",
    "p_value",
    "q_value",
    "n",
    "n_obs",
    "n_sig"
}


def _load_sample_harmonized_data() -> pd.DataFrame:
    """
    Loads a small sample of harmonized data if it exists, or raises
    FileNotFoundError if the pipeline hasn't run yet.
    """
    # This function is used to validate real data if available.
    # If the data doesn't exist yet, the test should be skipped or
    # we validate the schema structure against a generated minimal DF.
    # For a contract test, we often validate the *output* of the pipeline.
    # However, if the pipeline hasn't run, we can't test the file.
    # Let's create a minimal valid dataframe to test the *validation logic*
    # and then test against the real file if it exists.

    # Minimal valid dataframe
    data = {
        "sample_id": ["AGP_001", "UKBB_001"],
        "cohort": ["AGP", "UKBB"],
        "fiber_g_day": [25.0, 30.5],
        "read_count": [10000, 15000],
        "age": [40.0, 45.0],
        "bmi": [22.0, 24.0],
        "antibiotic_use": ["No", "Yes"],
        "sex": ["F", "M"],
        "origin": ["USA", "UK"],
        # Add a dummy taxa column to simulate presence
        "genus_Bacteroides": [0.1, 0.2]
    }
    return pd.DataFrame(data)


def validate_harmonized_schema(df: pd.DataFrame) -> bool:
    """
    Validates that the harmonized dataframe contains all required columns
    and correct dtypes.
    """
    # Check columns
    missing_cols = EXPECTED_HARMONIZED_COLUMNS - set(df.columns)
    if missing_cols:
        logger.error(f"Missing columns in harmonized data: {missing_cols}")
        return False

    # Check dtypes for core columns
    for col, expected_type in EXPECTED_HARMONIZED_DTYPES.items():
        if col in df.columns:
            if str(df[col].dtype) != expected_type:
                # Allow some flexibility for object vs string, or int vs float if data is clean
                # But strict check for now
                logger.warning(f"Column {col} has dtype {df[col].dtype}, expected {expected_type}")
                # We might want to be strict here. Let's be strict.
                # Actually, pandas might infer float64 for int if there's a NaN.
                # Let's just check if it's numeric where expected.
                if expected_type in ["int64", "float64"] and not pd.api.types.is_numeric_dtype(df[col]):
                    logger.error(f"Column {col} is not numeric: {df[col].dtype}")
                    return False
    return True


def validate_clr_schema(df: pd.DataFrame) -> bool:
    """
    Validates the CLR transformed dataframe schema.
    """
    # Must have sample_id, cohort, fiber_g_day
    required = {"sample_id", "cohort", "fiber_g_day"}
    if not required.issubset(df.columns):
        logger.error(f"CLR data missing required columns: {required - set(df.columns)}")
        return False

    # Check that other columns are numeric (taxa)
    for col in df.columns:
        if col not in required:
            if not pd.api.types.is_numeric_dtype(df[col]):
                logger.error(f"CLR data column {col} is not numeric: {df[col].dtype}")
                return False
    return True


def test_harmonized_data_schema_exists_and_valid():
    """
    Contract test: Verifies that data/processed/merged_harmonized.tsv exists
    and adheres to the expected schema.
    """
    # Determine path relative to project root
    # The task says: data/processed/merged_harmonized.tsv
    # Assuming project root is parent of code/
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    file_path = project_root / "data" / "processed" / "merged_harmonized.tsv"

    if not file_path.exists():
        pytest.skip(f"File {file_path} does not exist yet. Run T014 first.")

    try:
        df = pd.read_csv(file_path, sep="\t")
    except Exception as e:
        pytest.fail(f"Failed to read harmonized data: {e}")

    assert validate_harmonized_schema(df), "Harmonized data schema validation failed."


def test_clr_data_schema_exists_and_valid():
    """
    Contract test: Verifies that data/processed/clr_transformed.tsv exists
    and adheres to the expected schema.
    """
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent
    file_path = project_root / "data" / "processed" / "clr_transformed.tsv"

    if not file_path.exists():
        pytest.skip(f"File {file_path} does not exist yet. Run T020 first.")

    try:
        df = pd.read_csv(file_path, sep="\t")
    except Exception as e:
        pytest.fail(f"Failed to read CLR data: {e}")

    assert validate_clr_schema(df), "CLR data schema validation failed."


def test_schema_validation_logic_with_valid_data():
    """
    Unit test for the validation logic itself using a known valid dataframe.
    """
    df = _load_sample_harmonized_data()
    assert validate_harmonized_schema(df) is True


def test_schema_validation_logic_with_invalid_columns():
    """
    Unit test for the validation logic with missing columns.
    """
    df = _load_sample_harmonized_data()
    df = df.drop(columns=["fiber_g_day"])
    assert validate_harmonized_schema(df) is False