import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path to import synthetic_generator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))
from synthetic_generator import generate_synthetic_data, validate_schema

def test_generate_synthetic_data_mcar():
    """Test MCAR generation produces expected structure and missingness."""
    df, meta = generate_synthetic_data(
        n_samples=100,
        true_mean=50.0,
        true_variance=10.0,
        missingness_mechanism="MCAR",
        missing_rate=0.1,
        seed=42
    )
    
    assert len(df) == 100
    assert 'value' in df.columns
    assert 'id' in df.columns
    assert 'covariate' in df.columns
    assert meta['missingness_mechanism'] == "MCAR"
    assert abs(meta['true_mean'] - 50.0) < 1e-5
    assert abs(meta['true_variance'] - 10.0) < 1e-5
    
    # Check missing rate is approximately 10%
    missing_count = df['value'].isna().sum()
    assert abs(missing_count - 10) <= 2 # Allow small variance in random sampling

def test_generate_synthetic_data_mar():
    """Test MAR generation produces expected structure and missingness."""
    df, meta = generate_synthetic_data(
        n_samples=100,
        true_mean=50.0,
        true_variance=10.0,
        missingness_mechanism="MAR",
        missing_rate=0.1,
        seed=42
    )
    
    assert len(df) == 100
    assert 'covariate' in df.columns
    assert meta['missingness_mechanism'] == "MAR"
    
    # In MAR, missingness should be correlated with covariate
    # We can't easily test the exact correlation without knowing the implementation details,
    # but we ensure the mechanism runs without error and produces missing values.
    missing_count = df['value'].isna().sum()
    assert missing_count > 0

def test_invalid_mechanism():
    """Test that invalid mechanism raises error."""
    with pytest.raises(ValueError):
        generate_synthetic_data(missingness_mechanism="INVALID")
