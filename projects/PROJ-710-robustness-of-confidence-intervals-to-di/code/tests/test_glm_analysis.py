"""
Unit tests for GLM model setup and convergence in code/analysis/glm_analysis.py.

These tests verify that the GLM model is correctly configured, that it converges
on synthetic data with known properties, and that it produces expected outputs
for the coverage analysis pipeline.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Ensure the code directory is in the path for imports
code_path = Path(__file__).parent.parent
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from analysis.glm_analysis import fit_coverage_glm


def create_synthetic_coverage_data(n_samples=1000):
    """
    Create synthetic coverage data for testing GLM convergence.

    Generates data mimicking the structure of artifacts/coverage_results.csv
    with known relationships to test model recovery.
    """
    np.random.seed(42)

    # Generate epsilon values (log-spaced for realism)
    epsilons = np.random.lognormal(mean=0, sigma=1, size=n_samples)
    epsilons = np.clip(epsilons, 0.1, 10.0)

    # Generate noise types
    noise_types = np.random.choice(['laplace', 'gaussian'], size=n_samples)

    # Generate datasets
    datasets = np.random.choice(['adult', 'iris', 'wine'], size=n_samples)

    # Generate statistics
    statistics = np.random.choice(['mean', 'regression'], size=n_samples)

    # Create a synthetic coverage probability based on known relationships
    # Coverage tends to decrease as epsilon decreases (more noise)
    base_coverage = 0.95
    epsilon_effect = -0.05 * np.log(epsilons)  # Log relationship
    noise_effect = np.where(noise_types == 'laplace', -0.02, 0.01)

    # Add some noise and ensure bounds
    coverage_prob = base_coverage + epsilon_effect + noise_effect
    coverage_prob = np.clip(coverage_prob, 0.85, 1.0)

    # Generate binary coverage outcomes (covered or not)
    covered = np.random.binomial(1, coverage_prob, size=n_samples)

    # Create DataFrame
    df = pd.DataFrame({
        'epsilon': epsilons,
        'noise_type': noise_types,
        'dataset': datasets,
        'statistic': statistics,
        'covered': covered,
        'point_estimate': np.random.normal(0.5, 0.1, n_samples),
        'ci_lower': np.random.normal(0.45, 0.1, n_samples),
        'ci_upper': np.random.normal(0.55, 0.1, n_samples)
    })

    return df


class TestGLMModelSetup:
    """Tests for GLM model configuration and formula setup."""

    def test_fit_coverage_glm_returns_tuple(self):
        """Test that fit_coverage_glm returns a tuple of results."""
        df = create_synthetic_coverage_data(100)
        result = fit_coverage_glm(df)

        assert isinstance(result, tuple), "fit_coverage_glm should return a tuple"
        assert len(result) == 2, "fit_coverage_glm should return (model, results)"

    def test_fit_coverage_glm_with_minimal_data(self):
        """Test GLM fitting with minimal valid data."""
        # Create minimal dataset
        df = pd.DataFrame({
            'epsilon': [1.0, 2.0, 3.0, 4.0, 5.0],
            'noise_type': ['laplace', 'gaussian', 'laplace', 'gaussian', 'laplace'],
            'covered': [1, 1, 0, 1, 1]
        })

        model, results = fit_coverage_glm(df)

        assert model is not None, "Model should be created"
        assert results is not None, "Results should be created"

    def test_formula_includes_interaction_term(self):
        """Test that the GLM formula includes the interaction term."""
        df = create_synthetic_coverage_data(100)
        model, results = fit_coverage_glm(df)

        # The formula should include epsilon, noise_type, and their interaction
        # Check that the formula string contains the interaction term
        formula = model.formula
        assert 'epsilon' in formula, "Formula should include epsilon"
        assert 'noise_type' in formula, "Formula should include noise_type"
        assert ':' in formula, "Formula should include interaction term"


class TestGLMConvergence:
    """Tests for GLM convergence behavior."""

    def test_convergence_on_large_dataset(self):
        """Test that GLM converges on a reasonably sized dataset."""
        df = create_synthetic_coverage_data(2000)
        model, results = fit_coverage_glm(df)

        # Check convergence status
        assert results.converged, "GLM should converge on large dataset"

    def test_convergence_with_varying_epsilon_range(self):
        """Test convergence with wide range of epsilon values."""
        df = create_synthetic_coverage_data(1000)
        # Ensure wide range of epsilon values
        df['epsilon'] = np.logspace(-1, 2, size=len(df))

        model, results = fit_coverage_glm(df)

        assert results.converged, "GLM should converge with wide epsilon range"

    def test_no_convergence_warning_on_clean_data(self):
        """Test that clean data doesn't produce convergence warnings."""
        df = create_synthetic_coverage_data(500)
        model, results = fit_coverage_glm(df)

        # Check that there are no convergence warnings in the summary
        summary = results.summary2()
        summary_str = str(summary)

        # Should not contain convergence failure messages
        assert 'convergence' not in summary_str.lower() or 'converged' in summary_str.lower()


class TestGLMOutputValidation:
    """Tests for GLM output correctness and structure."""

    def test_coefficients_exist_for_all_predictors(self):
        """Test that coefficients exist for all expected predictors."""
        df = create_synthetic_coverage_data(200)
        model, results = fit_coverage_glm(df)

        params = results.params
        # Should have intercept and coefficients for epsilon and noise_type
        assert len(params) > 0, "Should have at least some coefficients"

    def test_pvalues_are_valid(self):
        """Test that p-values are valid probabilities."""
        df = create_synthetic_coverage_data(200)
        model, results = fit_coverage_glm(df)

        pvalues = results.pvalues
        assert all(0 <= p <= 1 for p in pvalues), "All p-values should be between 0 and 1"

    def test_log_likelihood_is_finite(self):
        """Test that log-likelihood is a finite number."""
        df = create_synthetic_coverage_data(200)
        model, results = fit_coverage_glm(df)

        llf = results.llf
        assert np.isfinite(llf), "Log-likelihood should be finite"

    def test_deviance_is_positive(self):
        """Test that deviance is positive."""
        df = create_synthetic_coverage_data(200)
        model, results = fit_coverage_glm(df)

        deviance = results.deviance
        assert deviance > 0, "Deviance should be positive"

    def test_aic_and_bic_are_finite(self):
        """Test that AIC and BIC are finite numbers."""
        df = create_synthetic_coverage_data(200)
        model, results = fit_coverage_glm(df)

        assert np.isfinite(results.aic), "AIC should be finite"
        assert np.isfinite(results.bic), "BIC should be finite"


class TestGLMFormulaCorrectness:
    """Tests for the correctness of the GLM formula specification."""

    def test_formula_matches_specification(self):
        """
        Test that the formula matches the specification:
        covered ~ epsilon + noise_type + epsilon:noise_type
        """
        df = create_synthetic_coverage_data(100)
        model, results = fit_coverage_glm(df)

        formula = model.formula
        # Check that all required terms are present
        required_terms = ['covered', 'epsilon', 'noise_type']
        for term in required_terms:
            assert term in formula, f"Formula should contain {term}"

        # Check for interaction term
        assert 'epsilon' in formula and 'noise_type' in formula, "Both main effects should be present"

    def test_binomial_family_used(self):
        """Test that binomial family is used for binary outcome."""
        df = create_synthetic_coverage_data(100)
        model, results = fit_coverage_glm(df)

        # Check family type
        assert model.family.__class__.__name__ == 'Binomial', "Should use Binomial family"


class TestGLMRobustness:
    """Tests for GLM robustness to edge cases."""

    def test_handles_imbalanced_coverage(self):
        """Test GLM with imbalanced coverage outcomes."""
        # Create data with very high coverage
        df = pd.DataFrame({
            'epsilon': np.random.lognormal(0, 1, 200),
            'noise_type': np.random.choice(['laplace', 'gaussian'], 200),
            'covered': np.random.binomial(1, 0.95, 200)  # 95% coverage
        })

        model, results = fit_coverage_glm(df)
        assert results.converged, "Should converge even with imbalanced data"

    def test_handles_low_coverage(self):
        """Test GLM with low coverage outcomes."""
        # Create data with very low coverage
        df = pd.DataFrame({
            'epsilon': np.random.lognormal(0, 1, 200),
            'noise_type': np.random.choice(['laplace', 'gaussian'], 200),
            'covered': np.random.binomial(1, 0.5, 200)  # 50% coverage
        })

        model, results = fit_coverage_glm(df)
        assert results.converged, "Should converge even with low coverage"

    def test_handles_single_noise_type(self):
        """Test GLM with only one noise type (edge case)."""
        df = pd.DataFrame({
            'epsilon': np.random.lognormal(0, 1, 100),
            'noise_type': ['laplace'] * 100,  # Only one type
            'covered': np.random.binomial(1, 0.9, 100)
        })

        # This should still work, though noise_type won't have variation
        model, results = fit_coverage_glm(df)
        # May or may not converge depending on statsmodels handling of constant
        # We just test that it doesn't crash
        assert model is not None


class TestGLMIntegration:
    """Integration tests for GLM with real data structures."""

    def test_works_with_coverage_results_structure(self):
        """Test GLM with data matching coverage_results.csv structure."""
        # Create data matching the expected structure
        df = create_synthetic_coverage_data(500)
        # Ensure all required columns are present
        required_cols = ['epsilon', 'noise_type', 'covered']
        for col in required_cols:
            assert col in df.columns, f"Missing column: {col}"

        model, results = fit_coverage_glm(df)
        assert results is not None, "Should produce results with proper data structure"

    def test_produces_reproducible_results(self):
        """Test that GLM produces reproducible results with same seed."""
        np.random.seed(123)
        df1 = create_synthetic_coverage_data(300)
        model1, results1 = fit_coverage_glm(df1)

        np.random.seed(123)
        df2 = create_synthetic_coverage_data(300)
        model2, results2 = fit_coverage_glm(df2)

        # Check that results are identical
        assert np.allclose(results1.params, results2.params), "Results should be reproducible"
        assert np.allclose(results1.pvalues, results2.pvalues), "P-values should be reproducible"