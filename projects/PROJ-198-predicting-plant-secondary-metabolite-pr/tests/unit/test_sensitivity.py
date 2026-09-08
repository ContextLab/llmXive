"""
Unit tests for sensitivity analysis functionality (T030b).

Tests the run_sensitivity_sweep and retrain_with_thresholds functions.
"""
import os
import sys
import tempfile
import pytest
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from modeling.eval import run_sensitivity_sweep, retrain_with_thresholds


@pytest.fixture
def sample_aligned_data(tmp_path):
    """Create a sample aligned dataset for testing."""
    # Create synthetic data that mimics the aligned matrix structure
    np.random.seed(42)
    n_samples = 20
    n_bgc_features = 5
    n_met_features = 3

    data = {
        'species': [f'Species_{i}' for i in range(n_samples)]
    }

    # Add BGC features
    for i in range(n_bgc_features):
        data[f'bgc_type_{i}'] = np.random.rand(n_samples) * 10

    # Add PCA features (simulated)
    for i in range(3):
        data[f'pca_{i}'] = np.random.rand(n_samples) * 5

    # Add metabolite features
    for i in range(n_met_features):
        data[f'log_met_{i}'] = np.random.rand(n_samples) * 2

    df = pd.DataFrame(data)

    # Save to temp file
    output_path = tmp_path / 'aligned_matrix.csv'
    df.to_csv(output_path, index=False)

    return output_path


@pytest.fixture
def sample_metrics_path(tmp_path):
    """Create a temporary metrics file path."""
    return tmp_path / 'metrics.json'


class TestRetrainWithThresholds:
    """Tests for retrain_with_thresholds function."""

    def test_retrain_basic(self, sample_aligned_data, tmp_path):
        """Test basic retraining with a single threshold."""
        output_path = tmp_path / 'threshold_results.json'

        results = retrain_with_thresholds(
            data_path=sample_aligned_data,
            thresholds=[0.5],
            model_type='rf',
            output_path=output_path
        )

        assert 0.5 in results
        assert 'r2' in results[0.5]
        assert isinstance(results[0.5]['r2'], (float, type(None)))

    def test_retrain_multiple_thresholds(self, sample_aligned_data, tmp_path):
        """Test retraining with multiple thresholds."""
        thresholds = [0.1, 0.3, 0.5]
        output_path = tmp_path / 'threshold_results.json'

        results = retrain_with_thresholds(
            data_path=sample_aligned_data,
            thresholds=thresholds,
            model_type='rf',
            output_path=output_path
        )

        for t in thresholds:
            assert t in results
            assert 'r2' in results[t]

    def test_retrain_invalid_model_type(self, sample_aligned_data):
        """Test that invalid model type raises error."""
        with pytest.raises(ValueError, match="Unknown model type"):
            retrain_with_thresholds(
                data_path=sample_aligned_data,
                thresholds=[0.5],
                model_type='invalid_model'
            )

    def test_retrain_output_file_created(self, sample_aligned_data, tmp_path):
        """Test that output file is created."""
        output_path = tmp_path / 'test_output.json'

        retrain_with_thresholds(
            data_path=sample_aligned_data,
            thresholds=[0.5],
            model_type='rf',
            output_path=output_path
        )

        assert output_path.exists()

        # Verify JSON content
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert '0.5' in data or 0.5 in data


class TestRunSensitivitySweep:
    """Tests for run_sensitivity_sweep function."""

    def test_sweep_basic(self, sample_aligned_data, tmp_path):
        """Test basic sensitivity sweep."""
        output_path = tmp_path / 'sensitivity_results.json'
        metrics_path = tmp_path / 'metrics.json'

        results = run_sensitivity_sweep(
            data_path=sample_aligned_data,
            thresholds=[0.1, 0.3, 0.5],
            model_type='rf',
            output_path=output_path,
            metrics_path=metrics_path
        )

        # Check structure
        assert 'thresholds' in results
        assert 'r2_by_threshold' in results
        assert 'n_successful' in results
        assert 'n_total' in results

        # Check threshold list
        assert results['thresholds'] == [0.1, 0.3, 0.5]

    def test_sweep_output_file_created(self, sample_aligned_data, tmp_path):
        """Test that output file is created."""
        output_path = tmp_path / 'sensitivity_test.json'

        run_sensitivity_sweep(
            data_path=sample_aligned_data,
            thresholds=[0.5],
            output_path=output_path
        )

        assert output_path.exists()

        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'thresholds' in data

    def test_sweep_metrics_update(self, sample_aligned_data, tmp_path):
        """Test that metrics file is updated."""
        output_path = tmp_path / 'sensitivity.json'
        metrics_path = tmp_path / 'metrics.json'

        # Create initial metrics
        initial_metrics = {'existing_key': 'value'}
        with open(metrics_path, 'w') as f:
            json.dump(initial_metrics, f)

        run_sensitivity_sweep(
            data_path=sample_aligned_data,
            thresholds=[0.5],
            output_path=output_path,
            metrics_path=metrics_path
        )

        # Verify metrics file updated
        with open(metrics_path, 'r') as f:
            updated_metrics = json.load(f)

        assert 'existing_key' in updated_metrics
        assert 'sensitivity_analysis' in updated_metrics

    def test_sweep_variation_calculation(self, sample_aligned_data, tmp_path):
        """Test that variation metrics are calculated."""
        output_path = tmp_path / 'sensitivity.json'

        results = run_sensitivity_sweep(
            data_path=sample_aligned_data,
            thresholds=[0.1, 0.3, 0.5, 0.7],
            output_path=output_path
        )

        # Check variation fields exist
        if results['n_successful'] >= 2:
            assert 'r2_range' in results
            assert 'variation_pass' in results
            assert 'max_difference' in results
            assert results['threshold_limit'] == 0.05

    def test_sweep_no_data_file(self, tmp_path):
        """Test behavior when data file doesn't exist."""
        non_existent = tmp_path / 'non_existent.csv'
        output_path = tmp_path / 'output.json'

        # Should handle gracefully or raise appropriate error
        # The function should log an error and return
        # We test that it doesn't crash unexpectedly
        with pytest.raises(FileNotFoundError):
            run_sensitivity_sweep(
                data_path=non_existent,
                thresholds=[0.5],
                output_path=output_path
            )

    def test_sweep_different_models(self, sample_aligned_data, tmp_path):
        """Test sweep with different model types."""
        output_path = tmp_path / 'sensitivity_rf.json'

        results_rf = run_sensitivity_sweep(
            data_path=sample_aligned_data,
            thresholds=[0.5],
            model_type='rf',
            output_path=output_path
        )

        assert 'r2_by_threshold' in results_rf
