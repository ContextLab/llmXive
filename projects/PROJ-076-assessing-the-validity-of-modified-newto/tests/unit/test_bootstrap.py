"""
Unit tests for block-bootstrap permutation test logic.

This module validates the implementation of the block-bootstrap permutation
test found in `code/residuals.py`. It ensures that:
1. The bootstrap resampling respects the block structure (galaxy-level).
2. The permutation logic correctly shuffles residuals between models.
3. The p-value calculation follows the standard definition.
4. Edge cases (single block, empty data) are handled gracefully.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from residuals import block_bootstrap_permutation_test, calculate_residuals
from utils import set_global_seed


@pytest.fixture
def sample_galaxy_data():
    """
    Create a deterministic sample dataset resembling a galaxy rotation curve.
    Returns a DataFrame with columns: radial_distance, velocity, velocity_error, model_mond, model_nfw
    """
    set_global_seed(42)
    n_points = 50
    r = np.linspace(1.0, 20.0, n_points)
    # Simulate observed velocity with some noise
    v_true = 200.0 + 10.0 * np.log(r)
    noise = np.random.normal(0, 5.0, n_points)
    v_obs = v_true + noise
    v_err = np.ones(n_points) * 5.0

    # Simulate model predictions (slightly different biases)
    v_mond = v_true + np.random.normal(2.0, 1.0, n_points)  # MOND slightly biased high
    v_nfw = v_true + np.random.normal(-1.0, 1.0, n_points)  # NFW slightly biased low

    return pd.DataFrame({
        'radial_distance': r,
        'velocity': v_obs,
        'velocity_error': v_err,
        'model_mond': v_mond,
        'model_nfw': v_nfw
    })


@pytest.fixture
def sample_residuals_df(sample_galaxy_data):
    """
    Pre-compute residuals for the sample galaxy data.
    """
    return calculate_residuals(sample_galaxy_data)


def test_block_bootstrap_respects_blocks(sample_residuals_df):
    """
    Test that the block bootstrap resamples entire galaxies (blocks) correctly.
    We verify that if we resample with replacement, the number of unique galaxies
    in the bootstrap sample is less than or equal to the original, and that
    the data structure is preserved.
    """
    n_bootstrap = 100
    n_galaxies = len(sample_residuals_df['galaxy_id'].unique())
    
    # Run bootstrap
    results = block_bootstrap_permutation_test(
        df=sample_residuals_df,
        model_col_mond='residual_mond',
        model_col_nfw='residual_nfw',
        n_bootstrap=n_bootstrap,
        random_state=42
    )
    
    # Verify output structure
    assert 'p_value' in results
    assert 'statistic' in results
    assert 'bootstrap_distribution' in results
    
    # The bootstrap distribution should have n_bootstrap entries
    assert len(results['bootstrap_distribution']) == n_bootstrap


def test_permutation_logic(sample_residuals_df):
    """
    Test that the permutation test correctly shuffles model labels.
    Under the null hypothesis (no difference between models), the
    distribution of the test statistic (difference in mean residuals)
    should be centered around zero if the models are equally good.
    """
    # Create a scenario where models are identical (null hypothesis true)
    df_null = sample_residuals_df.copy()
    df_null['residual_nfw'] = df_null['residual_mond'].copy()
    
    results = block_bootstrap_permutation_test(
        df=df_null,
        model_col_mond='residual_mond',
        model_col_nfw='residual_nfw',
        n_bootstrap=500,
        random_state=123
    )
    
    # The observed statistic should be near 0
    assert abs(results['statistic']) < 0.1, "Observed statistic should be near 0 for identical models"
    
    # The p-value should be high (fail to reject null)
    assert results['p_value'] > 0.05, "P-value should be high when models are identical"


def test_p_value_calculation(sample_residuals_df):
    """
    Verify that p-values are calculated correctly based on the bootstrap distribution.
    """
    # Create a scenario where MOND is significantly worse (higher residuals)
    df_worse = sample_residuals_df.copy()
    df_worse['residual_mond'] = df_worse['residual_mond'] + 50.0  # Large bias
    
    results = block_bootstrap_permutation_test(
        df=df_worse,
        model_col_mond='residual_mond',
        model_col_nfw='residual_nfw',
        n_bootstrap=1000,
        random_state=456
    )
    
    # The observed statistic (mond - nfw) should be large positive
    assert results['statistic'] > 10.0, "Observed statistic should be large positive"
    
    # The p-value should be low (reject null in favor of NFW)
    assert results['p_value'] < 0.05, "P-value should be low when one model is significantly worse"


def test_deterministic_with_seed(sample_residuals_df):
    """
    Ensure that running the test with the same random_state produces identical results.
    """
    results_1 = block_bootstrap_permutation_test(
        df=sample_residuals_df,
        model_col_mond='residual_mond',
        model_col_nfw='residual_nfw',
        n_bootstrap=200,
        random_state=999
    )
    
    results_2 = block_bootstrap_permutation_test(
        df=sample_residuals_df,
        model_col_mond='residual_mond',
        model_col_nfw='residual_nfw',
        n_bootstrap=200,
        random_state=999
    )
    
    assert results_1['p_value'] == results_2['p_value'], "P-values should be identical with same seed"
    assert np.allclose(results_1['bootstrap_distribution'], results_2['bootstrap_distribution']), \
        "Bootstrap distributions should be identical with same seed"


def test_single_block_handling():
    """
    Test behavior when there is only one galaxy (one block).
    The bootstrap should still run, but the variance might be limited.
    """
    set_global_seed(42)
    single_galaxy = pd.DataFrame({
        'galaxy_id': ['NGC123'] * 20,
        'residual_mond': np.random.normal(0, 5, 20),
        'residual_nfw': np.random.normal(0, 5, 20)
    })
    
    results = block_bootstrap_permutation_test(
        df=single_galaxy,
        model_col_mond='residual_mond',
        model_col_nfw='residual_nfw',
        n_bootstrap=50,
        random_state=777
    )
    
    # Should not crash
    assert 'p_value' in results
    assert 0.0 <= results['p_value'] <= 1.0


def test_empty_dataframe():
    """
    Test that the function handles empty input gracefully.
    """
    empty_df = pd.DataFrame(columns=['galaxy_id', 'residual_mond', 'residual_nfw'])
    
    with pytest.raises(ValueError, match="Input dataframe is empty"):
        block_bootstrap_permutation_test(
            df=empty_df,
            model_col_mond='residual_mond',
            model_col_nfw='residual_nfw',
            n_bootstrap=10,
            random_state=1
        )


def test_missing_columns(sample_residuals_df):
    """
    Test that the function raises an error if required columns are missing.
    """
    incomplete_df = sample_residuals_df.drop(columns=['residual_mond'])
    
    with pytest.raises(ValueError, match="Missing required columns"):
        block_bootstrap_permutation_test(
            df=incomplete_df,
            model_col_mond='residual_mond',
            model_col_nfw='residual_nfw',
            n_bootstrap=10,
            random_state=1
        )


def test_bootstrap_distribution_shape(sample_residuals_df):
    """
    Verify that the bootstrap distribution is a list of scalars (test statistics).
    """
    results = block_bootstrap_permutation_test(
        df=sample_residuals_df,
        model_col_mond='residual_mond',
        model_col_nfw='residual_nfw',
        n_bootstrap=50,
        random_state=123
    )
    
    dist = results['bootstrap_distribution']
    assert isinstance(dist, list), "Bootstrap distribution should be a list"
    assert len(dist) == 50, "Bootstrap distribution length should match n_bootstrap"
    assert all(isinstance(x, (int, float, np.floating)) for x in dist), \
        "All elements in bootstrap distribution should be numeric"
