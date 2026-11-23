"""
Unit tests for T010a: Real metrics computation script.

Tests verify:
1. Metrics are computed correctly for preprocessed real series
2. Output JSON format is correct
3. Edge cases (too short series) are handled properly
"""
import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from scripts.run_metrics_real import find_preprocessed_datasets, compute_metrics_for_real_datasets
from src.data.metrics import compute_all_metrics


@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)

    # Create a valid preprocessed dataset
    valid_data = pd.DataFrame({
        'value': np.random.randn(1000),
        'date': pd.date_range('2020-01-01', periods=1000, freq='H')
    })
    valid_data = valid_data.set_index('date')
    valid_file = processed_dir / "valid_series.csv"
    valid_data.to_csv(valid_file)

    # Create a short dataset (edge case)
    short_data = pd.DataFrame({
        'value': np.random.randn(20),
        'date': pd.date_range('2020-01-01', periods=20, freq='H')
    })
    short_data = short_data.set_index('date')
    short_file = processed_dir / "short_series.csv"
    short_data.to_csv(short_file)

    return {
        'processed_dir': processed_dir,
        'valid_file': valid_file,
        'short_file': short_file,
        'tmp_path': tmp_path
    }


class TestMetricsComputation:
    """Tests for metrics computation logic."""

    def test_find_preprocessed_datasets(self, temp_test_dir):
        """Test that find_preprocessed_datasets correctly identifies files."""
        datasets = find_preprocessed_datasets(temp_test_dir['processed_dir'])
        assert len(datasets) == 2
        assert temp_test_dir['valid_file'] in datasets
        assert temp_test_dir['short_file'] in datasets

    def test_compute_metrics_for_valid_series(self, temp_test_dir):
        """Test metrics computation on a valid series."""
        output_path = temp_test_dir['tmp_path'] / "output" / "metrics.json"

        datasets = find_preprocessed_datasets(temp_test_dir['processed_dir'])
        results = compute_metrics_for_real_datasets(datasets, output_path)

        assert results['summary']['successful'] == 1
        assert results['summary']['skipped_too_short'] == 1

        # Check valid dataset metrics
        valid_metrics = results['datasets']['valid_series']
        assert valid_metrics['status'] == 'success'
        assert 'metrics' in valid_metrics
        assert 'ACF_lag1' in valid_metrics['metrics']
        assert 'Hurst_exponent' in valid_metrics['metrics']
        assert 'Spectral_peak_ratio' in valid_metrics['metrics']

    def test_edge_case_too_short(self, temp_test_dir):
        """Test that short datasets are skipped with a warning."""
        output_path = temp_test_dir['tmp_path'] / "output" / "metrics.json"

        datasets = find_preprocessed_datasets(temp_test_dir['processed_dir'])
        results = compute_metrics_for_real_datasets(datasets, output_path)

        assert results['summary']['skipped_too_short'] == 1
        assert results['datasets']['short_series']['status'] == 'skipped'
        assert results['datasets']['short_series']['reason'] == 'too_short'


class TestMetricsOutputFormat:
    """Tests for the output JSON format."""

    def test_output_structure(self, temp_test_dir):
        """Test that the output JSON has the correct structure."""
        output_path = temp_test_dir['tmp_path'] / "output" / "metrics.json"

        datasets = find_preprocessed_datasets(temp_test_dir['processed_dir'])
        compute_metrics_for_real_datasets(datasets, output_path)

        # Load and validate JSON
        with open(output_path, 'r') as f:
            data = json.load(f)

        # Check top-level keys
        assert 'metadata' in data
        assert 'datasets' in data
        assert 'summary' in data

        # Check metadata
        assert data['metadata']['task_id'] == 'T010a'
        assert 'ACF' in data['metadata']['description']
        assert 'Hurst' in data['metadata']['description']
        assert 'Spectral' in data['metadata']['description']

        # Check summary keys
        assert 'total_datasets' in data['summary']
        assert 'successful' in data['summary']
        assert 'skipped_too_short' in data['summary']
        assert 'errors' in data['summary']

    def test_metrics_values_are_numeric(self, temp_test_dir):
        """Test that computed metrics are numeric values."""
        output_path = temp_test_dir['tmp_path'] / "output" / "metrics.json"

        datasets = find_preprocessed_datasets(temp_test_dir['processed_dir'])
        compute_metrics_for_real_datasets(datasets, output_path)

        with open(output_path, 'r') as f:
            data = json.load(f)

        valid_metrics = data['datasets']['valid_series']['metrics']

        # Check that all metrics are numeric
        assert isinstance(valid_metrics['ACF_lag1'], (int, float))
        assert isinstance(valid_metrics['Hurst_exponent'], (int, float))
        assert isinstance(valid_metrics['Spectral_peak_ratio'], (int, float))

        # Check reasonable ranges
        assert -1 <= valid_metrics['ACF_lag1'] <= 1
        assert 0 <= valid_metrics['Hurst_exponent'] <= 1
        assert valid_metrics['Spectral_peak_ratio'] >= 0
