"""
Contract test for data/processed/features.csv schema (Task T035a).
Validates the output of T012c.
"""
import os
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))
import sys

from config import get_path

REQUIRED_COLUMNS = [
    'participant_id', 
    'median_rt', 
    'delta_rel', 
    'theta_rel', 
    'alpha_rel', 
    'low_beta_rel', 
    'high_beta_rel', 
    'gamma_rel'
]

RT_MIN = 100
RT_MAX = 2000

@pytest.fixture
def features_path():
    return get_path("processed", "features.csv")

def test_schema_exists(features_path):
    """Test that the features.csv file exists."""
    assert os.path.exists(features_path), f"Features file not found at {features_path}"

def test_schema_columns(features_path):
    """Test that all required columns exist."""
    df = pd.read_csv(features_path)
    assert set(df.columns) == set(REQUIRED_COLUMNS), \
        f"Columns mismatch. Expected: {REQUIRED_COLUMNS}, Got: {list(df.columns)}"

def test_schema_no_nulls(features_path):
    """Test that there are no null values in the dataframe."""
    df = pd.read_csv(features_path)
    assert df.isnull().sum().sum() == 0, "Found null values in features.csv"

def test_schema_rt_range(features_path):
    """Test that median_rt is within valid range [100, 2000]."""
    df = pd.read_csv(features_path)
    assert (df['median_rt'] >= RT_MIN).all(), f"Found median_rt < {RT_MIN}"
    assert (df['median_rt'] <= RT_MAX).all(), f"Found median_rt > {RT_MAX}"

def test_schema_relative_power_range(features_path):
    """Test that relative power values are between 0 and 1."""
    df = pd.read_csv(features_path)
    rel_cols = ['delta_rel', 'theta_rel', 'alpha_rel', 'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    for col in rel_cols:
        assert (df[col] >= 0).all(), f"Found negative values in {col}"
        assert (df[col] <= 1).all(), f"Found values > 1 in {col}"
        # Check that sum of relative powers is approximately 1 (allowing for floating point errors)
        # sum(df[col] for col in rel_cols) should be close to 1 for each row
        row_sums = df[rel_cols].sum(axis=1)
        assert (row_sums > 0.99).all() and (row_sums < 1.01).all(), \
            f"Relative power sum not close to 1 for some rows. Min: {row_sums.min()}, Max: {row_sums.max()}"
