"""
Unit tests for sensitivity analysis module.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json

from modeling.sensitivity import (
    load_feature_importance_data,
    calculate_permutation_p_values,
    analyze_threshold_sensitivity,
    generate_sensitivity_report
)
from utils.exceptions import DataQualityError

class TestLoadFeatureImportanceData:
    """Tests for load_feature_importance_data function."""

    def test_load_valid_csv(self, tmp_path):
        """Test loading a valid feature importance CSV file."""
        # Create test data
        test_data = pd.DataFrame({
            'feature': ['soil_n', 'soil_p', 'soil_k', 'ph'],
            'importance': [0.25, 0.20, 0.15, 0.10]
        })

        # Write to temp file
        csv_path = tmp_path / "feature_importance.csv"
        test_data.to_csv(csv_path, index=False)

        # Load and verify
        result = load_feature_importance_data.__globals__['FEATURE_IMPORTANCE_CSV'] = csv_path
        # We need to patch the global variable
        with patch('modeling.sensitivity.FEATURE_IMPORTANCE_CSV', csv_path):
            result = load_feature_importance_data()

        assert len(result) == 4
        assert list(result.columns) == ['feature', 'importance']
        assert 'soil_n' in result['feature'].values

    def test_missing_file_raises_error(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        csv_path = tmp_path / "nonexistent.csv"

        with patch('modeling.sensitivity.FEATURE_IMPORTANCE_CSV', csv_path):
            with pytest.raises(FileNotFoundError):
                load_feature_importance_data()

    def test_missing_columns_raises_error(self, tmp_path):
        """Test that missing required columns raises ValueError."""
        test_data = pd.DataFrame({
            'feature': ['soil_n', 'soil_p'],
            'other_col': [0.25, 0.20]
        })

        csv_path = tmp_path / "invalid.csv"
        test_data.to_csv(csv_path, index=False)

        with patch('modeling.sensitivity.FEATURE_IMPORTANCE_CSV', csv_path):
            with pytest.raises(ValueError):
                load_feature_importance_data()

class TestCalculatePermutationPValues:
    """Tests for calculate_permutation_p_values function."""

    def test_p_values_calculated_correctly(self):
        """Test that p-values are calculated for each feature."""
        # Create mock model
        mock_model = Mock()
        mock_model.predict = Mock(return_value=np.array([1.0, 2.0, 3.0, 4.0, 5.0]))

        # Create mock data
        X = pd.DataFrame({
            'feature_a': [1, 2, 3, 4, 5],
            'feature_b': [2, 3, 4, 5, 6]
        })
        y = pd.Series([1.5, 2.5, 3.5, 4.5, 5.5])

        feature_df = pd.DataFrame({
            'feature': ['feature_a', 'feature_b'],
            'importance': [0.1, 0.05]
        })

        # Mock r2_score to return consistent values
        with patch('modeling.sensitivity.r2_score') as mock_r2:
            mock_r2.side_effect = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2]  # baseline + permutations

            result = calculate_permutation_p_values(
                model=mock_model,
                X=X,
                y=y,
                feature_importance_df=feature_df,
                n_permutations=5,
                random_state=42
            )

        assert len(result) == 2
        assert 'p_value' in result.columns
        assert 'is_significant' in result.columns
        assert all(0 <= p <= 1 for p in result['p_value'])

    def test_features_not_in_data_handled(self):
        """Test that features not in training data are skipped."""
        mock_model = Mock()
        mock_model.predict = Mock(return_value=np.array([1.0, 2.0, 3.0, 4.0, 5.0]))

        X = pd.DataFrame({
            'feature_a': [1, 2, 3, 4, 5]
        })
        y = pd.Series([1.5, 2.5, 3.5, 4.5, 5.5])

        feature_df = pd.DataFrame({
            'feature': ['feature_a', 'feature_not_in_data'],
            'importance': [0.1, 0.05]
        })

        with patch('modeling.sensitivity.r2_score') as mock_r2:
            mock_r2.side_effect = [0.9, 0.8, 0.7, 0.6, 0.5]

            result = calculate_permutation_p_values(
                model=mock_model,
                X=X,
                y=y,
                feature_importance_df=feature_df,
                n_permutations=3,
                random_state=42
            )

        # Should only have one result for feature_a
        assert len(result) == 1
        assert result['feature'].iloc[0] == 'feature_a'

class TestAnalyzeThresholdSensitivity:
    """Tests for analyze_threshold_sensitivity function."""

    def test_threshold_analysis(self):
        """Test that sensitivity analysis is performed across thresholds."""
        p_value_results = pd.DataFrame({
            'feature': ['f1', 'f2', 'f3', 'f4', 'f5'],
            'importance': [0.5, 0.4, 0.3, 0.2, 0.1],
            'p_value': [0.01, 0.03, 0.07, 0.12, 0.25],
            'is_significant': [True, True, False, False, False]
        })

        thresholds = [0.05, 0.10, 0.15]
        result = analyze_threshold_sensitivity(p_value_results, thresholds)

        assert len(result) == 3
        assert list(result.columns) == ['threshold', 'n_significant', 'top_1', 'top_2', 'top_3', 'top_3_features']

        # Check threshold 0.05: f1 and f2 are significant, top 1 should be f1
        row_005 = result[result['threshold'] == 0.05].iloc[0]
        assert row_005['n_significant'] == 2
        assert row_005['top_1'] == 'f1'

    def test_empty_significant_features(self):
        """Test handling when no features are significant."""
        p_value_results = pd.DataFrame({
            'feature': ['f1', 'f2'],
            'importance': [0.1, 0.05],
            'p_value': [0.5, 0.6],
            'is_significant': [False, False]
        })

        result = analyze_threshold_sensitivity(p_value_results, [0.05])

        assert len(result) == 1
        assert result['n_significant'].iloc[0] == 0
        assert result['top_1'].iloc[0] is None

class TestGenerateSensitivityReport:
    """Tests for generate_sensitivity_report function."""

    def test_report_generation(self, tmp_path):
        """Test that a valid markdown report is generated."""
        p_value_results = pd.DataFrame({
            'feature': ['f1', 'f2'],
            'importance': [0.5, 0.3],
            'p_value': [0.01, 0.08],
            'is_significant': [True, False]
        })

        sensitivity_df = pd.DataFrame({
            'threshold': [0.05, 0.10],
            'n_significant': [1, 2],
            'top_1': ['f1', 'f1'],
            'top_2': [None, 'f2'],
            'top_3': [None, None],
            'top_3_features': ['f1', 'f1, f2']
        })

        output_path = tmp_path / "test_report.md"
        generate_sensitivity_report(p_value_results, sensitivity_df, output_path)

        assert output_path.exists()

        with open(output_path, 'r') as f:
            content = f.read()

        # Check for required sections
        assert "## Threshold Stability" in content
        assert "## Justification" in content
        assert "0.05 chosen based on typical significance levels" in content
        assert "f1" in content
        assert "associational" in content.lower()

    def test_report_contains_citation(self, tmp_path):
        """Test that the report contains the required citation."""
        p_value_results = pd.DataFrame({
            'feature': ['f1'],
            'importance': [0.5],
            'p_value': [0.01],
            'is_significant': [True]
        })

        sensitivity_df = pd.DataFrame({
            'threshold': [0.05],
            'n_significant': [1],
            'top_1': ['f1'],
            'top_2': [None],
            'top_3': [None],
            'top_3_features': ['f1']
        })

        output_path = tmp_path / "test_report.md"
        generate_sensitivity_report(p_value_results, sensitivity_df, output_path)

        with open(output_path, 'r') as f:
            content = f.read()

        assert "0.05 chosen based on typical significance levels in ecological regression" in content