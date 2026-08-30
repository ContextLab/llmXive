import json
import os
import tempfile
import pytest
import pandas as pd
import numpy as np

from code.data.synthetic import generate_synthetic_data, validate_schema

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_synthetic_produces_known_variance():
    """
    Test that the synthetic generator produces data with variance
    close to the specified true_variance within a tolerance.
    """
    n = 100000  # Large sample to ensure statistical convergence
    true_mean = 50.0
    true_variance = 25.0
    missing_rate = 0.0  # No missingness for variance check to avoid bias from imputation logic
    mechanism = 'MCAR'
    seed = 42

    df, meta = generate_synthetic_data(
        n=n,
        true_mean=true_mean,
        true_variance=true_variance,
        missing_rate=missing_rate,
        mechanism=mechanism,
        seed=seed
    )

    # Check metadata
    assert meta['true_mean'] == true_mean
    assert meta['true_variance'] == true_variance
    assert meta['missingness_mechanism'] == mechanism

    # Calculate observed variance (ddof=1 for sample variance)
    # Since missing_rate is 0, all values are present
    observed_variance = df['value'].var(ddof=1)

    # Tolerance: 1% of true variance is reasonable for n=100k
    tolerance = 0.01 * true_variance
    assert abs(observed_variance - true_variance) < tolerance, \
        f"Observed variance {observed_variance} differs from true {true_variance} by more than tolerance {tolerance}"

def test_synthetic_schema_validation():
    """
    Test that the generated data conforms to the expected schema.
    """
    df, meta = generate_synthetic_data(
        n=1000,
        true_mean=10.0,
        true_variance=4.0,
        missing_rate=0.1,
        mechanism='MAR',
        seed=123
    )

    # Validate against schema
    is_valid = validate_schema(df, meta)
    assert is_valid is True

    # Check specific columns
    assert 'id' in df.columns
    assert 'value' in df.columns
    assert 'missingness_mechanism' in df.columns

def test_synthetic_missingness_rate():
    """
    Test that the actual missingness rate is close to the specified rate.
    """
    n = 10000
    true_mean = 50.0
    true_variance = 25.0
    target_missing_rate = 0.2
    mechanism = 'MCAR'
    seed = 999

    df, meta = generate_synthetic_data(
        n=n,
        true_mean=true_mean,
        true_variance=true_variance,
        missing_rate=target_missing_rate,
        mechanism=mechanism,
        seed=seed
    )

    actual_missing_rate = df['value'].isna().sum() / n
    # Allow 5% absolute tolerance for random variation
    assert abs(actual_missing_rate - target_missing_rate) < 0.05, \
        f"Actual missing rate {actual_missing_rate} differs from target {target_missing_rate}"
