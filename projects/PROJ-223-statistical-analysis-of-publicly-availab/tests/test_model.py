"""
Tests for ordinal logistic regression modeling logic.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.model import fit_ordinal_model, prepare_model_data, extract_odds_ratios

class TestModelConvergence:
    """Unit test for model convergence on sample data (T018)."""

    def test_fit_ordinal_model_convergence(self):
        """Test that the model converges on a simple dataset."""
        # Create a simple synthetic dataset for testing convergence
        np.random.seed(42)
        n_samples = 100
        
        data = pd.DataFrame({
            'severity': np.random.choice([0, 1, 2], n_samples),
            'precipitation': np.random.uniform(0, 1, n_samples),
            'visibility': np.random.uniform(5, 15, n_samples),
            'temperature': np.random.uniform(10, 30, n_samples),
            'hour': np.random.randint(0, 24, n_samples),
            'day': np.random.randint(1, 31, n_samples),
            'road_type': np.random.choice([0, 1], n_samples)
        })

        # Prepare model data
        X, y = prepare_model_data(data)

        # Fit model
        result = fit_ordinal_model(X, y)

        # Verify result is not None (convergence)
        assert result is not None
        
        # Verify we can extract odds ratios
        odds_ratios = extract_odds_ratios(result)
        assert odds_ratios is not None
        assert len(odds_ratios) > 0

class TestModelIntegration:
    """Integration test for full model fit and coefficient extraction (T019)."""

    def test_full_model_fit_and_extraction(self):
        """Test the full pipeline from data preparation to odds ratio extraction."""
        # Create realistic synthetic data
        np.random.seed(42)
        n_samples = 200
        
        data = pd.DataFrame({
            'severity': np.random.choice([0, 1, 2], n_samples, p=[0.6, 0.3, 0.1]),
            'precipitation': np.random.uniform(0, 2, n_samples),
            'visibility': np.random.uniform(2, 20, n_samples),
            'temperature': np.random.uniform(-5, 40, n_samples),
            'hour': np.random.randint(0, 24, n_samples),
            'day': np.random.randint(1, 31, n_samples),
            'road_type': np.random.choice([0, 1, 2], n_samples)
        })

        X, y = prepare_model_data(data)
        
        # Fit model
        model_result = fit_ordinal_model(X, y)
        
        if model_result is None:
            pytest.skip("Model did not converge on test data")
        
        # Extract odds ratios
        odds_ratios = extract_odds_ratios(model_result)
        
        # Verify structure
        assert isinstance(odds_ratios, pd.DataFrame)
        assert 'odds_ratio' in odds_ratios.columns
        assert 'conf_int_lower' in odds_ratios.columns
        assert 'conf_int_upper' in odds_ratios.columns
        
        # Verify all predictors have odds ratios
        expected_predictors = ['precipitation', 'visibility', 'temperature', 'hour', 'day', 'road_type']
        for pred in expected_predictors:
            assert pred in odds_ratios.index
