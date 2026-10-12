"""
Test that the final_features.csv file is produced and contains the expected
engineered columns without null values.
"""

import pandas as pd
import pytest
from llmxive_toolkit import paths

REQUIRED_COLUMNS = [
    "mean_atomic_radius",
    "electronegativity_variance",
    "vec",
    "atomic_number_variance",
    "temperature",
    "material_family",
]

@pytest.fixture(scope="session")
def final_features_df():
    """Load the final_features.csv dataset."""
    csv_path = paths.data("processed", "final_features.csv")
    # The file should exist; if not, the test will raise an informative error.
    assert csv_path.is_file(), f"{csv_path} does not exist"
    return pd.read_csv(csv_path)

def test_final_features_columns(final_features_df):
    """Check that all required columns are present."""
    missing = [col for col in REQUIRED_COLUMNS if col not in final_features_df.columns]
    assert not missing, f"Missing required columns: {missing}"

def test_no_nulls_in_engineered_columns(final_features_df):
    """Ensure there are no null values in engineered feature columns."""
    null_counts = final_features_df[REQUIRED_COLUMNS].isnull().sum()
    cols_with_null = null_counts[null_counts > 0].index.tolist()
    assert not cols_with_null, f"Null values found in columns: {cols_with_null}"