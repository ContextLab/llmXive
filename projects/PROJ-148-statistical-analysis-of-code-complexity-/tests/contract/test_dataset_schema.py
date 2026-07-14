"""
Contract test for dataset schema (US1).
Ensures the dataset produced by the pipeline adheres to the defined schema.
"""
import pytest
import pandas as pd

# Expected columns based on data-model.md and task requirements
EXPECTED_COLUMNS = {
    "cc",  # Cyclomatic Complexity
    "loc",  # Lines of Code
    "tokens",  # Token count
    "nesting_depth",  # Nesting depth
    "halstead_volume",  # Halstead volume
    "bug_label",  # Binary label
    "project_id",  # Project identifier
    "file_path",  # Source file path
    "function_name",  # Function name
}


def test_dataset_schema(df_dataset: pd.DataFrame):
    """
    Contract test: Verify the dataset has the required columns.
    This assumes a fixture `df_dataset` provides the real pipeline output.
    If the fixture is missing, this test is skipped or marked as pending.
    """
    if df_dataset is None:
        pytest.skip("Dataset fixture not available (pipeline not run).")

    actual_columns = set(df_dataset.columns)
    missing = EXPECTED_COLUMNS - actual_columns

    assert not missing, f"Dataset missing required columns: {missing}"

    # Verify types for key columns
    assert df_dataset["bug_label"].dtype in ["int64", "int32", "bool"]
    assert df_dataset["project_id"].dtype == "object"
