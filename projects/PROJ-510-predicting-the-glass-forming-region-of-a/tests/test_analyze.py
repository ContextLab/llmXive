"""
Unit and integration tests for analysis and sensitivity (User Story 3).
Tests for T028, T029, T031, T032, and T027 (integration test for sensitivity analysis).
"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import json
from unittest.mock import patch, MagicMock
from sklearn.ensemble import RandomForestRegressor

# Ensure code directory is in path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from analyze import (
    load_model_and_data,
    analyze_feature_importance,
    run_sensitivity_analysis,
    run_analysis
)

class TestAnalyze:
    """Tests for analysis pipeline."""

    def test_load_model_and_data(self):
        """Test loading model and data."""
        # Create temporary files
        model_file = "test_temp_model.pkl"
        data_file = "test_temp_data.csv"
        
        # Create dummy model
        model = RandomForestRegressor()
        import pickle
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)

        # Create dummy data
        data = {
            'mixing_enthalpy': [1.0, 2.0, 3.0],
            'atomic_size_mismatch': [1.0, 2.0, 3.0],
            'electronegativity_variance': [1.0, 2.0, 3.0],
            'critical_cooling_rate': [100.0, 200.0, 300.0]
        }
        pd.DataFrame(data).to_csv(data_file, index=False)

        loaded_model, loaded_data = load_model_and_data(model_file, data_file)

        assert isinstance(loaded_model, RandomForestRegressor)
        assert isinstance(loaded_data, pd.DataFrame)
        assert len(loaded_data) == 3

        # Cleanup
        os.remove(model_file)
        os.remove(data_file)

    def test_analyze_feature_importance(self):
        """Test feature importance analysis."""
        # Create synthetic data
        X = pd.DataFrame({
            'mixing_enthalpy': np.random.randn(100),
            'atomic_size_mismatch': np.random.randn(100),
            'electronegativity_variance': np.random.randn(100)
        })
        y = np.random.randn(100)

        model = RandomForestRegressor(random_state=42)
        model.fit(X, y)

        importance_results = analyze_feature_importance(model, X, y, n_permutations=5, random_state=42)

        assert isinstance(importance_results, dict)
        assert 'importance_ranking' in importance_results
        assert 'p_values' in importance_results
        assert len(importance_results['importance_ranking']) == 3

    def test_run_sensitivity_analysis(self):
        """Test sensitivity analysis across thresholds."""
        # Create synthetic data
        X = pd.DataFrame({
            'mixing_enthalpy': np.random.randn(100),
            'atomic_size_mismatch': np.random.randn(100),
            'electronegativity_variance': np.random.randn(100)
        })
        y = np.random.randn(100) * 100 + 100 # Shift to positive range

        model = RandomForestRegressor(random_state=42)
        model.fit(X, y)

        thresholds = [50, 100, 150]
        sensitivity_results = run_sensitivity_analysis(model, X, y, thresholds)

        assert isinstance(sensitivity_results, dict)
        assert 'threshold_values' in sensitivity_results
        assert 'f1_scores' in sensitivity_results
        assert len(sensitivity_results['threshold_values']) == 3
        assert len(sensitivity_results['f1_scores']) == 3

    def test_sensitivity_analysis_integration_t027(self):
        """
        Integration test for sensitivity analysis across thresholds {50, 100, 150} K/s.
        Asserts that the output JSON contains the correct keys and values.
        """
        # Create synthetic data
        X = pd.DataFrame({
            'mixing_enthalpy': np.random.randn(200),
            'atomic_size_mismatch': np.random.randn(200),
            'electronegativity_variance': np.random.randn(200)
        })
        y = np.random.randn(200) * 100 + 100

        model = RandomForestRegressor(random_state=42)
        model.fit(X, y)

        thresholds = [50, 100, 150]
        sensitivity_results = run_sensitivity_analysis(model, X, y, thresholds)

        # Assert structure
        assert isinstance(sensitivity_results, dict)
        assert 'threshold_values' in sensitivity_results
        assert 'f1_scores' in sensitivity_results
        assert 'rmse_values' in sensitivity_results

        # Assert values match expected thresholds
        assert sensitivity_results['threshold_values'] == thresholds
        assert len(sensitivity_results['f1_scores']) == 3
        assert len(sensitivity_results['rmse_values']) == 3

        # Assert F1 scores are valid probabilities
        for f1 in sensitivity_results['f1_scores']:
            assert 0.0 <= f1 <= 1.0

        # Assert RMSE values are non-negative
        for rmse in sensitivity_results['rmse_values']:
            assert rmse >= 0

    @patch('analyze.load_model_and_data')
    @patch('analyze.analyze_feature_importance')
    @patch('analyze.run_sensitivity_analysis')
    @patch('analyze.json.dump')
    @patch('analyze.os.makedirs')
    def test_run_analysis(self, mock_makedirs, mock_json, mock_sens, mock_imp, mock_load):
        """Test the full analysis pipeline execution."""
        # Mock inputs
        mock_model = MagicMock(spec=RandomForestRegressor)
        mock_data = pd.DataFrame({'a': [1, 2]})
        mock_load.return_value = (mock_model, mock_data)
        
        mock_imp.return_value = {'importance_ranking': ['x'], 'p_values': [0.01]}
        mock_sens.return_value = {'threshold_values': [50], 'f1_scores': [0.8]}

        # Run analysis
        run_analysis()

        # Verify calls
        mock_load.assert_called_once()
        mock_imp.assert_called_once()
        mock_sens.assert_called_once()
        mock_makedirs.assert_called()
        mock_json.assert_called()

if __name__ == '__main__':
    pytest.main([__file__, "-v"])