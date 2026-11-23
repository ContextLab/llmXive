"""Tests for T023d: Model Metrics Aggregation."""
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the function to test
from modeling import aggregate_model_metrics, METRICS_PATH


class TestAggregateModelMetrics:
    """Test the aggregation of model metrics from CV and test sets."""

    def test_aggregate_metrics_structure(self):
        """Test that aggregated metrics contain all required fields."""
        cv_metrics = {
            'cv_mae': 0.045,
            'cv_std': 0.005,
            'cv_ci_lower': 0.035,
            'cv_ci_upper': 0.055
        }
        test_metrics = {
            'test_mae': 0.048,
            'residuals': [0.01, -0.02, 0.005],
            'y_true': [0.35, 0.36, 0.34],
            'y_pred': [0.34, 0.38, 0.335]
        }

        result = aggregate_model_metrics(cv_metrics, test_metrics)

        # Check required fields exist
        assert 'cv_mae' in result
        assert 'cv_ci_lower' in result
        assert 'cv_ci_upper' in result
        assert 'test_mae' in result

        # Check values are correct
        assert result['cv_mae'] == 0.045
        assert result['cv_ci_lower'] == 0.035
        assert result['cv_ci_upper'] == 0.055
        assert result['test_mae'] == 0.048

    def test_aggregate_metrics_types(self):
        """Test that all aggregated values are numeric."""
        cv_metrics = {
            'cv_mae': 0.045,
            'cv_std': 0.005,
            'cv_ci_lower': 0.035,
            'cv_ci_upper': 0.055
        }
        test_metrics = {
            'test_mae': 0.048,
            'residuals': [],
            'y_true': [],
            'y_pred': []
        }

        result = aggregate_model_metrics(cv_metrics, test_metrics)

        assert isinstance(result['cv_mae'], float)
        assert isinstance(result['cv_ci_lower'], float)
        assert isinstance(result['cv_ci_upper'], float)
        assert isinstance(result['test_mae'], float)

    def test_aggregate_metrics_edge_cases(self):
        """Test aggregation with edge case values."""
        # Zero values
        cv_metrics = {
            'cv_mae': 0.0,
            'cv_std': 0.0,
            'cv_ci_lower': 0.0,
            'cv_ci_upper': 0.0
        }
        test_metrics = {
            'test_mae': 0.0,
            'residuals': [],
            'y_true': [],
            'y_pred': []
        }

        result = aggregate_model_metrics(cv_metrics, test_metrics)
        assert result['cv_mae'] == 0.0
        assert result['test_mae'] == 0.0

        # Large values
        cv_metrics = {
            'cv_mae': 1.0,
            'cv_std': 0.5,
            'cv_ci_lower': -0.5,
            'cv_ci_upper': 2.5
        }
        test_metrics = {
            'test_mae': 1.2,
            'residuals': [],
            'y_true': [],
            'y_pred': []
        }

        result = aggregate_model_metrics(cv_metrics, test_metrics)
        assert result['cv_mae'] == 1.0
        assert result['test_mae'] == 1.2

    def test_save_model_metrics_creates_file(self, tmp_path):
        """Test that save_model_metrics creates the expected file."""
        from modeling import save_model_metrics

        # Temporarily override METRICS_PATH
        test_path = tmp_path / "model_metrics.json"
        with patch('modeling.METRICS_PATH', test_path):
            metrics = {
                'cv_mae': 0.045,
                'cv_ci_lower': 0.035,
                'cv_ci_upper': 0.055,
                'test_mae': 0.048
            }
            save_model_metrics(metrics)

            # Verify file exists
            assert test_path.exists()

            # Verify content
            with open(test_path, 'r') as f:
                loaded = json.load(f)

            assert loaded == metrics

    def test_aggregated_metrics_match_schema(self, tmp_path):
        """Test that aggregated metrics match the expected schema."""
        cv_metrics = {
            'cv_mae': 0.045,
            'cv_std': 0.005,
            'cv_ci_lower': 0.035,
            'cv_ci_upper': 0.055
        }
        test_metrics = {
            'test_mae': 0.048,
            'residuals': [],
            'y_true': [],
            'y_pred': []
        }

        result = aggregate_model_metrics(cv_metrics, test_metrics)

        # Schema check: must have exactly these keys
        required_keys = {'cv_mae', 'cv_ci_lower', 'cv_ci_upper', 'test_mae'}
        assert set(result.keys()) == required_keys

        # All values must be numeric
        for key, value in result.items():
            assert isinstance(value, (int, float)), f"Value for {key} is not numeric"
            assert not (isinstance(value, float) and (value != value)), f"Value for {key} is NaN"