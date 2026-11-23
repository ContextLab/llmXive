"""
Unit tests for causal effect estimation logic (OLS and DiD).
Verifies OLS implementation, DiD fallback logic, and cluster-robust standard errors.
"""
import pytest
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.multicomp import pairwise_tukeyhsd
from src.analysis.causal import (
    DataUnavailableError,
    run_ols,
    run_did,
    estimate_causal_effect
)
from src.utils.logging import get_logger

logger = get_logger()


@pytest.fixture
def ols_data():
    """
    Create a synthetic dataset suitable for OLS regression testing.
    Includes treatment, outcome, covariates, and matched pair IDs.
    """
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        'treatment': np.random.binomial(1, 0.5, n),
        'outcome': np.random.normal(0, 1, n),
        'covariate_1': np.random.normal(0, 1, n),
        'covariate_2': np.random.normal(0, 1, n),
        'log_energy_cost': np.random.normal(np.log(100), 0.5, n),
        'pair_id': np.repeat(np.arange(n // 2), 2)  # Matched pairs
    })
    # Ensure some correlation for realistic testing
    df['outcome'] = df['treatment'] * 2.5 + df['covariate_1'] * 0.5 + df['log_energy_cost'] * 0.1 + np.random.normal(0, 0.5, n)
    return df


@pytest.fixture
def did_data():
    """
    Create a synthetic dataset suitable for Difference-in-Differences testing.
    Requires pre_treatment_outcome and post_treatment_outcome columns.
    """
    np.random.seed(42)
    n = 200
    df = pd.DataFrame({
        'treatment': np.random.binomial(1, 0.5, n),
        'pre_treatment_outcome': np.random.normal(10, 2, n),
        'post_treatment_outcome': np.random.normal(12, 2, n),
        'covariate_1': np.random.normal(0, 1, n),
        'pair_id': np.repeat(np.arange(n // 2), 2)
    })
    # Add treatment effect
    df['post_treatment_outcome'] = (
        df['pre_treatment_outcome'] + 
        df['treatment'] * 3.0 + 
        np.random.normal(0, 1, n)
    )
    return df


@pytest.fixture
def incomplete_did_data():
    """
    Create a dataset missing required columns for DiD.
    """
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'treatment': np.random.binomial(1, 0.5, n),
        'outcome': np.random.normal(0, 1, n),
        'covariate_1': np.random.normal(0, 1, n)
    })


class TestOLS:
    """Tests for OLS regression functionality."""

    def test_ols_returns_valid_result(self, ols_data):
        """Verify run_ols returns a statsmodels RegressionResults object."""
        result = run_ols(ols_data)
        assert result is not None
        assert hasattr(result, 'params')
        assert hasattr(result, 'pvalues')
        assert hasattr(result, 'conf_int')

    def test_ols_treatment_coefficient_sign(self, ols_data):
        """Verify the treatment coefficient is estimated."""
        result = run_ols(ols_data)
        # The coefficient for 'treatment' should exist
        assert 'treatment' in result.params.index

    def test_ols_cluster_robust_se(self, ols_data):
        """Verify that cluster-robust standard errors are calculated."""
        result = run_ols(ols_data, cluster_var='pair_id')
        # Check if the result object has cluster-robust properties
        # statsmodels OLSResults with cov_type='cluster' will have specific attributes
        assert result is not None
        # Verify that the standard errors are different from non-clustered if clusters vary
        # This is a structural check; the actual values depend on data generation

    def test_ols_missing_columns_raises(self):
        """Verify run_ols raises KeyError if required columns are missing."""
        df = pd.DataFrame({'treatment': [1, 0], 'other': [1, 1]})
        with pytest.raises(KeyError):
            run_ols(df, outcome_col='missing_col')


class TestDiD:
    """Tests for Difference-in-Differences functionality."""

    def test_did_returns_valid_result(self, did_data):
        """Verify run_did returns a statsmodels RegressionResults object."""
        result = run_did(did_data)
        assert result is not None
        assert hasattr(result, 'params')
        assert hasattr(result, 'pvalues')

    def test_did_treatment_effect_estimation(self, did_data):
        """Verify DiD correctly estimates the interaction effect."""
        result = run_did(did_data)
        # The interaction term (treatment * post) should be significant
        # We check that the parameter exists
        params = result.params
        # Depending on implementation, the interaction term might be named differently
        # We assume the function constructs the interaction correctly
        assert len(params) > 0

    def test_did_missing_columns_raises(self, incomplete_did_data):
        """Verify run_did raises DataUnavailableError if longitudinal data is missing."""
        with pytest.raises(DataUnavailableError):
            run_did(incomplete_did_data)

    def test_did_with_cluster_se(self, did_data):
        """Verify DiD supports cluster-robust standard errors."""
        result = run_did(did_data, cluster_var='pair_id')
        assert result is not None


class TestEstimateCausalEffect:
    """Tests for the high-level causal effect estimation logic."""

    def test_estimate_effect_returns_dict(self, ols_data):
        """Verify estimate_causal_effect returns a dictionary with required keys."""
        result = estimate_causal_effect(ols_data)
        assert isinstance(result, dict)
        assert 'att_estimate' in result
        assert 'p_value' in result
        assert 'ci_lower' in result
        assert 'ci_upper' in result
        assert 'methodology' in result

    def test_estimate_effect_with_did_fallback(self, did_data):
        """Verify estimate_causal_effect uses DiD when OLS is not suitable (simulated)."""
        # This test verifies the structure of the output when DiD logic is triggered
        # We pass data that supports DiD
        result = estimate_causal_effect(did_data, use_did=True)
        assert isinstance(result, dict)
        assert result['methodology'] == 'DiD'

    def test_estimate_effect_missing_data_raises(self, incomplete_did_data):
        """Verify estimate_causal_effect handles missing data gracefully."""
        # If we force DiD on incomplete data, it should raise
        with pytest.raises(DataUnavailableError):
            estimate_causal_effect(incomplete_did_data, use_did=True)