"""
Integration tests for significance testing functionality.

These tests verify that the significance testing module correctly:
1. Loads regression results and interaction terms
2. Calculates standard errors and p-values
3. Identifies significant interaction terms
4. Produces valid output files
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression

from code.services.significance_test import (
    load_regression_results,
    load_interaction_terms,
    calculate_standard_errors,
    calculate_p_values,
    run_significance_test,
    save_results,
    main
)
from code.errors import DataLoadError


class TestSignificanceTestIntegration:
    """Integration tests for significance testing."""

    @pytest.fixture
    def temp_processed_dir(self, tmp_path):
        """Create a temporary processed directory with test data."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)

        # Create test regression results
        regression_data = {
            'coefficients': {
                'Cr': 0.1,
                'Mo': 0.05,
                'Cr_Mo': 0.08,
                'Cr_V': 0.02,
                'Mo_V': 0.03
            },
            'feature_names': ['Cr', 'Mo', 'Cr_Mo', 'Cr_V', 'Mo_V'],
            'model_metrics': {
                'r2': 0.85,
                'mse': 0.02
            }
        }

        regression_path = processed_dir / "cooperative_effects_analysis.json"
        with open(regression_path, 'w') as f:
            json.dump(regression_data, f)

        # Create test interaction terms
        interaction_data = {
            'Cr': [0.1, 0.2, 0.3, 0.4, 0.5] * 20,
            'Mo': [0.05, 0.1, 0.15, 0.2, 0.25] * 20,
            'Cr_Mo': [0.005, 0.02, 0.045, 0.08, 0.125] * 20,
            'Cr_V': [0.01, 0.02, 0.03, 0.04, 0.05] * 20,
            'Mo_V': [0.0025, 0.005, 0.0075, 0.01, 0.0125] * 20,
            'segregation_energy': [0.15, 0.25, 0.35, 0.45, 0.55] * 20
        }

        interaction_df = pd.DataFrame(interaction_data)
        interaction_path = processed_dir / "interaction_terms.csv"
        interaction_df.to_csv(interaction_path, index=False)

        return processed_dir

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_load_regression_results_success(self, mock_processed_path, temp_processed_dir):
        """Test successful loading of regression results."""
        mock_processed_path.__truediv__.return_value = temp_processed_dir / "cooperative_effects_analysis.json"

        results = load_regression_results()

        assert 'coefficients' in results
        assert 'feature_names' in results
        assert len(results['coefficients']) == 5

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_load_regression_results_missing_file(self, mock_processed_path, tmp_path):
        """Test error handling when regression results file is missing."""
        mock_processed_path.__truediv__.return_value = tmp_path / "nonexistent.json"

        with pytest.raises(DataLoadError):
            load_regression_results()

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_load_interaction_terms_success(self, mock_processed_path, temp_processed_dir):
        """Test successful loading of interaction terms."""
        mock_processed_path.__truediv__.return_value = temp_processed_dir / "interaction_terms.csv"

        df = load_interaction_terms()

        assert isinstance(df, pd.DataFrame)
        assert 'segregation_energy' in df.columns
        assert len(df) == 100

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_run_significance_test(self, mock_processed_path, temp_processed_dir):
        """Test the full significance testing workflow."""
        mock_processed_path.__truediv__.return_value = temp_processed_dir

        # Load test data
        regression_data = load_regression_results()
        interaction_df = load_interaction_terms()

        # Run significance test
        results = run_significance_test(regression_data, interaction_df)

        # Verify results structure
        assert 'coefficients' in results
        assert 'p_values' in results
        assert 'standard_errors' in results
        assert 'significant_terms' in results
        assert 'summary' in results

        # Verify summary
        assert 'total_terms' in results['summary']
        assert 'significant_terms' in results['summary']
        assert results['summary']['total_terms'] == 5

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_calculate_standard_errors(self, mock_processed_path, temp_processed_dir):
        """Test standard error calculation."""
        mock_processed_path.__truediv__.return_value = temp_processed_dir

        coefficients = np.array([0.1, 0.05, 0.08, 0.02, 0.03])
        interaction_df = load_interaction_terms()

        feature_cols = [col for col in interaction_df.columns if col != 'segregation_energy']
        X = interaction_df[feature_cols].values
        y = interaction_df['segregation_energy'].values

        model = LinearRegression()
        model.fit(X, y)

        standard_errors = calculate_standard_errors(coefficients, X, y, model)

        assert len(standard_errors) == 5
        assert all(se > 0 for se in standard_errors)

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_calculate_p_values(self, mock_processed_path, temp_processed_dir):
        """Test p-value calculation."""
        mock_processed_path.__truediv__.return_value = temp_processed_dir

        coefficients = np.array([0.1, 0.05, 0.08, 0.02, 0.03])
        standard_errors = np.array([0.02, 0.015, 0.025, 0.01, 0.012])

        p_values = calculate_p_values(coefficients, standard_errors)

        assert len(p_values) == 5
        assert all(0 <= p <= 1 for p in p_values)

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_save_results(self, mock_processed_path, temp_processed_dir, tmp_path):
        """Test saving results to file."""
        mock_processed_path.__truediv__.return_value = temp_processed_dir

        regression_data = load_regression_results()
        interaction_df = load_interaction_terms()
        results = run_significance_test(regression_data, interaction_df)

        output_path = tmp_path / "test_significance_results.json"
        save_results(results, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            saved_results = json.load(f)

        assert 'coefficients' in saved_results
        assert 'p_values' in saved_results
        assert 'summary' in saved_results

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_main_function(self, mock_processed_path, temp_processed_dir, caplog):
        """Test the main function execution."""
        mock_processed_path.__truediv__.return_value = temp_processed_dir

        # Capture output
        with caplog.at_level('INFO'):
            main()

        # Verify log messages
        assert 'Starting significance testing' in caplog.text
        assert 'Significance test complete' in caplog.text

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_significant_term_detection(self, mock_processed_path, temp_processed_dir):
        """Test that significant terms are correctly identified."""
        mock_processed_path.__truediv__.return_value = temp_processed_dir

        regression_data = load_regression_results()
        interaction_df = load_interaction_terms()

        results = run_significance_test(regression_data, interaction_df)

        # Check that significant terms have p < 0.05
        for term in results['significant_terms']:
            if term['significant']:
                assert term['p_value'] < 0.05
            else:
                assert term['p_value'] >= 0.05

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_empty_regression_data(self, mock_processed_path, tmp_path):
        """Test handling of empty regression data."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)

        # Create empty regression results
        regression_path = processed_dir / "cooperative_effects_analysis.json"
        with open(regression_path, 'w') as f:
            json.dump({}, f)

        mock_processed_path.__truediv__.return_value = regression_path

        with pytest.raises(DataLoadError):
            load_regression_results()

    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_invalid_interaction_terms(self, mock_processed_path, tmp_path):
        """Test handling of invalid interaction terms."""
        processed_dir = tmp_path / "data" / "processed"
        processed_dir.mkdir(parents=True)

        # Create invalid interaction terms (missing target column)
        interaction_path = processed_dir / "interaction_terms.csv"
        pd.DataFrame({'Cr': [1, 2, 3]}).to_csv(interaction_path, index=False)

        mock_processed_path.__truediv__.return_value = interaction_path

        with pytest.raises((DataLoadError, KeyError)):
            load_interaction_terms()
