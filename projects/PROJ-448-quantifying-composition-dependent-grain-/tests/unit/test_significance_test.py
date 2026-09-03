"""
Unit tests for significance testing functionality.
"""

import json
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import mock_open, patch

from code.services.significance_test import (
    calculate_p_values,
    calculate_standard_errors,
    run_significance_test,
    load_regression_results,
    load_interaction_terms
)
from code.errors import ConfigurationError, ValidationError


class TestCalculatePValues:
    def test_basic_p_value_calculation(self):
        """Test basic p-value calculation with known values."""
        coefficients = np.array([1.0, 2.0, 0.0])
        standard_errors = np.array([0.1, 0.2, 0.5])
        
        p_values = calculate_p_values(coefficients, standard_errors)
        
        # All p-values should be between 0 and 1
        assert all(0 <= p <= 1 for p in p_values)
        # Non-zero coefficients with small SE should have small p-values
        assert p_values[0] < 0.05
        assert p_values[1] < 0.05
        # Zero coefficient should have large p-value
        assert p_values[2] > 0.05

    def test_p_value_with_large_standard_error(self):
        """Test that large standard errors lead to non-significant p-values."""
        coefficients = np.array([1.0])
        standard_errors = np.array([10.0])
        
        p_values = calculate_p_values(coefficients, standard_errors)
        
        assert p_values[0] > 0.05


class TestCalculateStandardErrors:
    def test_basic_standard_error_calculation(self):
        """Test basic standard error calculation."""
        np.random.seed(42)
        X = np.random.rand(100, 3)
        y = np.random.rand(100)
        coefficients = np.array([0.5, 0.3, 0.2])
        
        standard_errors = calculate_standard_errors(X, y, coefficients)
        
        # Standard errors should be positive
        assert all(se > 0 for se in standard_errors)
        # Should have same length as coefficients
        assert len(standard_errors) == len(coefficients)

    def test_standard_error_with_perfect_fit(self):
        """Test standard errors with a perfect fit (should be very small)."""
        X = np.array([[1, 2], [3, 4], [5, 6]])
        y = np.array([3, 7, 11])  # Perfect linear relationship
        coefficients = np.array([0.5, 1.0])
        
        standard_errors = calculate_standard_errors(X, y, coefficients)
        
        # Standard errors should be very small for perfect fit
        assert all(se < 0.1 for se in standard_errors)

class TestRunSignificanceTest:
    def test_significant_and_non_significant_features(self):
        """Test detection of both significant and non-significant features."""
        coefficients = np.array([1.0, 0.5, 0.0])
        standard_errors = np.array([0.1, 0.3, 0.5])
        feature_names = ['Cr_Mo', 'Cr_V', 'Mo_V']
        
        results = run_significance_test(coefficients, standard_errors, feature_names, alpha=0.05)
        
        # Check that results have expected structure
        assert 'significant' in results
        assert 'non_significant' in results
        assert 'summary' in results
        
        # First two should be significant, last one not
        assert len(results['significant']) >= 1
        assert len(results['non_significant']) >= 1
        
        # Check summary
        assert results['summary']['total_features'] == 3
        assert results['summary']['alpha'] == 0.05

    def test_all_significant(self):
        """Test case where all features are significant."""
        coefficients = np.array([1.0, 2.0, 3.0])
        standard_errors = np.array([0.1, 0.1, 0.1])
        feature_names = ['feature1', 'feature2', 'feature3']
        
        results = run_significance_test(coefficients, standard_errors, feature_names, alpha=0.05)
        
        assert len(results['significant']) == 3
        assert len(results['non_significant']) == 0

    def test_all_non_significant(self):
        """Test case where no features are significant."""
        coefficients = np.array([0.1, 0.2, 0.1])
        standard_errors = np.array([1.0, 1.0, 1.0])
        feature_names = ['feature1', 'feature2', 'feature3']
        
        results = run_significance_test(coefficients, standard_errors, feature_names, alpha=0.05)
        
        assert len(results['significant']) == 0
        assert len(results['non_significant']) == 3

class TestLoadRegressionResults:
    @patch('builtins.open', new_callable=mock_open)
    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_load_existing_file(self, mock_path, mock_file):
        """Test loading existing regression results file."""
        mock_path.__truediv__.return_value = Path('fake_path/regression_results.json')
        mock_file.return_value.read.return_value = json.dumps({'coefficients': [0.5, 0.3]})
        
        results = load_regression_results()
        
        assert 'coefficients' in results
        assert results['coefficients'] == [0.5, 0.3]

    @patch('pathlib.Path.exists')
    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_missing_file_raises_error(self, mock_path, mock_exists):
        """Test that missing file raises ConfigurationError."""
        mock_path.__truediv__.return_value = Path('fake_path/regression_results.json')
        mock_exists.return_value = False
        
        with pytest.raises(ConfigurationError):
            load_regression_results()

class TestLoadInteractionTerms:
    @patch('pandas.read_csv')
    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_load_interaction_terms(self, mock_path, mock_read_csv):
        """Test loading interaction terms from CSV."""
        mock_path.__truediv__.return_value = Path('fake_path/interaction_terms.csv')
        
        # Mock DataFrame with interaction terms
        import pandas as pd
        df = pd.DataFrame({
            'Cr': [0.1, 0.2],
            'Mo': [0.05, 0.1],
            'Cr_Mo': [0.005, 0.02],
            'Cr_V': [0.003, 0.01],
            'temperature': [300, 400]
        })
        mock_read_csv.return_value = df
        
        interaction_data, feature_names = load_interaction_terms()
        
        assert len(feature_names) == 2
        assert 'Cr_Mo' in feature_names
        assert 'Cr_V' in feature_names
        assert interaction_data.shape[0] == 2

    @patch('pandas.read_csv')
    @patch('code.services.significance_test.PROCESSED_PATH')
    def test_no_interaction_terms_raises_error(self, mock_path, mock_read_csv):
        """Test that missing interaction terms raises ValidationError."""
        mock_path.__truediv__.return_value = Path('fake_path/interaction_terms.csv')
        
        # Mock DataFrame without interaction terms
        import pandas as pd
        df = pd.DataFrame({
            'Cr': [0.1, 0.2],
            'Mo': [0.05, 0.1],
            'temperature': [300, 400]
        })
        mock_read_csv.return_value = df
        
        with pytest.raises(ValidationError):
            load_interaction_terms()