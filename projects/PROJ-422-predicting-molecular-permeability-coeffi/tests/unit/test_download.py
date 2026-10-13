import pytest
import pandas as pd

from code.data.download import DataLoader, VERIFIED_DATASET_CONFIG

def test_download_and_target_column():
    """
    Integration test that runs the DataLoader and asserts the required
    permeability target column is present and numeric.
    """
    loader = DataLoader()
    df = loader.process()  # This writes to data/raw/permeability_data.csv
    # Verify that the DataFrame contains the expected columns
    expected_cols = set(VERIFIED_DATASET_CONFIG["expected_columns"])
    assert expected_cols.issubset(set(df.columns)), f"Missing expected columns: {expected_cols - set(df.columns)}"

    # Verify the target column is numeric
    target = VERIFIED_DATASET_CONFIG["target_column"]
    assert pd.api.types.is_numeric_dtype(df[target]), f"Target column '{target}' is not numeric"
