"""
tests/contract/test_feature_schema.py
Validates the schema of data/processed/features.csv.
"""
import pytest
import pandas as pd
import os
from pathlib import Path

FEATURES_PATH = Path(__file__).parent.parent.parent / 'data' / 'processed' / 'features.csv'

def test_feature_schema_exists():
    """Check if the file exists."""
    assert FEATURES_PATH.exists(), f"File {FEATURES_PATH} does not exist."

def test_feature_schema_columns():
    """Check required columns."""
    if not FEATURES_PATH.exists():
        pytest.skip("File not found")
    
    df = pd.read_csv(FEATURES_PATH)
    required_cols = [
        'participant_id', 'median_rt', 
        'delta_rel', 'theta_rel', 'alpha_rel', 
        'low_beta_rel', 'high_beta_rel', 'gamma_rel'
    ]
    for col in required_cols:
        assert col in df.columns, f"Missing column: {col}"

def test_feature_schema_no_nulls():
    """Check for nulls."""
    if not FEATURES_PATH.exists():
        pytest.skip("File not found")
    
    df = pd.read_csv(FEATURES_PATH)
    assert df.isnull().sum().sum() == 0, "Found null values in features."

def test_feature_schema_rt_range():
    """Check RT physiological bounds (100ms to 2000ms)."""
    if not FEATURES_PATH.exists():
        pytest.skip("File not found")
    
    df = pd.read_csv(FEATURES_PATH)
    assert df['median_rt'].min() >= 0.1, "RT too low (min < 100ms)"
    assert df['median_rt'].max() <= 2.0, "RT too high (max > 2000ms)"
