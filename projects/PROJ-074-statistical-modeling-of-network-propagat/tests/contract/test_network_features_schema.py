"""
Contract test for network features output schema.

Verifies that intermediate_network_features.csv contains all required columns
and data types as specified in the data model.
"""

import json
import os
import pandas as pd
import pytest
from pathlib import Path

# Expected columns based on T015 specification
REQUIRED_COLUMNS = [
    "cascade_id",
    "degree_mean",
    "degree_std",
    "degree_skew",
    "degree_kurt",
    "clustering_coeff",
    "mean_betweenness"
]

@pytest.fixture
def features_file():
    """Path to the generated network features file."""
    return Path("results/intermediate_network_features.csv")


def test_file_exists(features_file):
    """Test that the network features file was created."""
    assert features_file.exists(), f"Network features file not found: {features_file}"


def test_required_columns(features_file):
    """Test that all required columns are present."""
    df = pd.read_csv(features_file)
    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    assert not missing, f"Missing required columns: {missing}"


def test_column_types(features_file):
    """Test that numeric columns are numeric."""
    df = pd.read_csv(features_file)

    numeric_cols = [
        "degree_mean", "degree_std", "degree_skew", "degree_kurt",
        "clustering_coeff", "mean_betweenness"
    ]

    for col in numeric_cols:
        if col in df.columns:
            assert pd.api.types.is_numeric_dtype(df[col]), \
                f"Column {col} is not numeric"


def test_no_missing_values(features_file):
    """Test that no required columns have missing values."""
    df = pd.read_csv(features_file)

    for col in REQUIRED_COLUMNS:
        if col in df.columns:
            assert not df[col].isna().any(), \
                f"Column {col} contains missing values"


def test_clustering_coeff_range(features_file):
    """Test that clustering coefficient is in valid range [0, 1]."""
    df = pd.read_csv(features_file)
    if "clustering_coeff" in df.columns:
        assert df["clustering_coeff"].min() >= 0.0
        assert df["clustering_coeff"].max() <= 1.0


def test_degree_metrics_non_negative(features_file):
    """Test that degree metrics are non-negative."""
    df = pd.read_csv(features_file)
    degree_cols = ["degree_mean", "degree_std"]
    for col in degree_cols:
        if col in df.columns:
            assert df[col].min() >= 0.0, f"Column {col} has negative values"


def test_schema_validation(features_file):
    """Comprehensive schema validation against contract."""
    df = pd.read_csv(features_file)

    # Check column count
    assert len(df.columns) >= len(REQUIRED_COLUMNS), \
        f"Expected at least {len(REQUIRED_COLUMNS)} columns, got {len(df.columns)}"

    # Check data types
    numeric_cols = [
        "degree_mean", "degree_std", "degree_skew", "degree_kurt",
        "clustering_coeff", "mean_betweenness"
    ]

    for col in numeric_cols:
        if col in df.columns:
            assert pd.api.types.is_numeric_dtype(df[col]), \
                f"Column {col} must be numeric"

    # Check for reasonable value ranges
    if "clustering_coeff" in df.columns:
        assert df["clustering_coeff"].min() >= 0.0
        assert df["clustering_coeff"].max() <= 1.0

    if "degree_mean" in df.columns:
        assert df["degree_mean"].min() >= 0.0

    if "degree_std" in df.columns:
        assert df["degree_std"].min() >= 0.0
