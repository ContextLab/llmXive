"""
Contract test for feature matrix schema.

Validates that data/processed/feature_matrix.csv adheres to the required schema:
- Columns: isolate_id, gene_presence_matrix, snp_counts, cnv_counts, resistance_phenotype
- Types and basic structural constraints.
"""

import os
import json
import pytest
import pandas as pd
from pathlib import Path

# Import config to locate paths dynamically
# Note: We assume the project root is the parent of 'tests'
# If running via pytest from root, this works directly.
sys_path = Path(__file__).resolve().parent.parent
if str(sys_path) not in os.sys.path:
    os.sys.path.insert(0, str(sys_path))

from utils.config import get_paths

REQUIRED_COLUMNS = [
    "isolate_id",
    "gene_presence_matrix",
    "snp_counts",
    "cnv_counts",
    "resistance_phenotype"
]

@pytest.fixture
def feature_matrix_path():
    """Locate the feature matrix file."""
    paths = get_paths()
    processed_dir = paths.get("processed_data_dir", "data/processed")
    file_path = Path(processed_dir) / "feature_matrix.csv"
    return file_path

@pytest.fixture
def feature_matrix_df(feature_matrix_path):
    """Load the feature matrix if it exists."""
    if not feature_matrix_path.exists():
        pytest.skip(f"Feature matrix not found at {feature_matrix_path}. "
                    "Run T016 (build_feature_matrix.py) first.")
    return pd.read_csv(feature_matrix_path)

def test_feature_matrix_exists(feature_matrix_path):
    """Contract: File must exist."""
    assert feature_matrix_path.exists(), (
        f"Feature matrix file missing at {feature_matrix_path}. "
        "Ensure T016 (build_feature_matrix.py) has been executed."
    )

def test_feature_matrix_columns(feature_matrix_df):
    """Contract: DataFrame must contain all required columns."""
    missing_cols = set(REQUIRED_COLUMNS) - set(feature_matrix_df.columns)
    assert not missing_cols, (
        f"Feature matrix is missing required columns: {missing_cols}. "
        f"Found columns: {list(feature_matrix_df.columns)}"
    )

def test_feature_matrix_non_empty(feature_matrix_df):
    """Contract: DataFrame must have at least one row."""
    assert len(feature_matrix_df) > 0, "Feature matrix is empty."

def test_isolate_id_uniqueness(feature_matrix_df):
    """Contract: isolate_id must be unique."""
    duplicates = feature_matrix_df[feature_matrix_df.duplicated(subset=["isolate_id"], keep=False)]
    assert len(duplicates) == 0, (
        f"Duplicate isolate_ids found: {duplicates['isolate_id'].unique().tolist()}"
    )

def test_no_missing_phenotype(feature_matrix_df):
    """Contract: resistance_phenotype must not have missing values."""
    assert feature_matrix_df["resistance_phenotype"].isnull().sum() == 0, (
        "Found missing values in 'resistance_phenotype' column."
    )

def test_gene_presence_matrix_format(feature_matrix_df):
    """Contract: gene_presence_matrix column should contain list-like or string representation of matrices."""
    # Depending on how build_feature_matrix.py serializes this, it might be a stringified list
    # or a JSON string. We check that it's not NaN and has content.
    for idx, val in feature_matrix_df["gene_presence_matrix"].items():
        if pd.isna(val):
            pytest.fail(f"Row {idx} has NaN in gene_presence_matrix.")
        # Basic check: it should look like a list or a JSON string
        val_str = str(val)
        assert len(val_str) > 2, f"Row {idx} gene_presence_matrix is empty or malformed."

def test_numeric_counts_valid(feature_matrix_df):
    """Contract: snp_counts and cnv_counts must be numeric."""
    for col in ["snp_counts", "cnv_counts"]:
        if not pd.api.types.is_numeric_dtype(feature_matrix_df[col]):
            # Attempt conversion to see if it's parseable strings
            try:
                feature_matrix_df[col] = pd.to_numeric(feature_matrix_df[col])
            except (ValueError, TypeError):
                pytest.fail(f"Column '{col}' contains non-numeric values that cannot be converted.")

def test_phenotype_values_valid(feature_matrix_df):
    """Contract: resistance_phenotype should be categorical (e.g., 'Resistant', 'Susceptible')."""
    valid_values = {"Resistant", "Susceptible", "Intermediate", "R", "S", "I"}
    unique_phenos = set(feature_matrix_df["resistance_phenotype"].unique())
    invalid_phenos = unique_phenos - valid_values

    # If we find invalid values, we fail the contract unless they are clearly empty strings
    invalid_clean = {p for p in invalid_phenos if p and str(p).strip() != ""}
    assert not invalid_clean, (
        f"Found invalid resistance phenotype values: {invalid_clean}. "
        f"Expected one of: {valid_values}"
    )