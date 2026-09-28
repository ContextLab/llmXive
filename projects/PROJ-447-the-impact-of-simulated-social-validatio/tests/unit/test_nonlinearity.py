"""
Unit Tests for Non-linearity Analysis (T026)

Tests the quadratic model fitting logic to ensure it correctly identifies
linear vs non-linear relationships and handles edge cases.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from analysis.nonlinearity import fit_quadratic_model, run_nonlinearity_analysis
from utils.exceptions import DataGapError


@pytest.fixture
def linear_data():
    """Generate data with a clear linear relationship (no quadratic effect)."""
    np.random.seed(42)
    n = 200
    x = np.random.normal(0, 1, n)
    # Linear relationship: y = 2*x + noise (no x^2 term)
    y = 2.0 * x + np.random.normal(0, 0.5, n)
    return pd.DataFrame({
        'perceived_social_validation': x,
        'self_perception_score': y,
        'age': np.random.normal(15, 2, n),
        'gender': np.random.choice([0, 1], n),
        'offline_relationships': np.random.normal(5, 1, n),
        'intrinsic_traits': np.random.normal(10, 2, n)
    })


@pytest.fixture
def quadratic_data():
    """Generate data with a clear quadratic relationship."""
    np.random.seed(42)
    n = 200
    x = np.random.normal(0, 1, n)
    # Quadratic relationship: y = 2*x + 1.5*x^2 + noise
    y = 2.0 * x + 1.5 * (x ** 2) + np.random.normal(0, 0.5, n)
    return pd.DataFrame({
        'perceived_social_validation': x,
        'self_perception_score': y,
        'age': np.random.normal(15, 2, n),
        'gender': np.random.choice([0, 1], n),
        'offline_relationships': np.random.normal(5, 1, n),
        'intrinsic_traits': np.random.normal(10, 2, n)
    })


@pytest.fixture
def empty_df():
    """Empty DataFrame for edge case testing."""
    return pd.DataFrame()


def test_quadratic_model_linear_data(linear_data):
    """Test that a linear dataset does NOT flag the quadratic term as significant."""
    model, results = fit_quadratic_model(linear_data)

    # The quadratic coefficient should be small and insignificant
    assert abs(results['quadratic_coeff']) < 1.0  # Should be close to 0
    assert not results['is_quadratic_significant']
    assert results['n_observations'] == 200


def test_quadratic_model_quadratic_data(quadratic_data):
    """Test that a quadratic dataset flags the quadratic term as significant."""
    model, results = fit_quadratic_model(quadratic_data)

    # The quadratic coefficient should be significant and positive (~1.5)
    assert results['is_quadratic_significant']
    assert results['quadratic_coeff'] > 1.0  # Should be close to 1.5
    assert results['n_observations'] == 200


def test_quadratic_model_empty_data(empty_df):
    """Test that empty data raises DataGapError."""
    with pytest.raises(DataGapError):
        fit_quadratic_model(empty_df)


def test_run_nonlinearity_analysis_saves_json(quadratic_data, tmp_path):
    """Test that run_nonlinearity_analysis saves results to JSON."""
    output_file = tmp_path / "test_nonlinearity.json"
    
    results = run_nonlinearity_analysis(
        quadratic_data,
        output_path=str(output_file)
    )

    # Verify file exists
    assert output_file.exists()

    # Verify content matches returned results
    with open(output_file, 'r') as f:
        saved_results = json.load(f)

    assert saved_results['is_quadratic_significant'] == results['is_quadratic_significant']
    assert 'quadratic_coeff' in saved_results
    assert 'quadratic_pvalue' in saved_results


def test_missing_columns_raises_error():
    """Test that missing required columns raises DataGapError."""
    df = pd.DataFrame({'other_col': [1, 2, 3]})
    
    with pytest.raises(DataGapError):
        fit_quadratic_model(df, outcome_col='missing_outcome', predictor_col='missing_pred')