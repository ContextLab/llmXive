"""
Unit tests for the analysis module.

Tests:
- calculate_metric_error: Verify error calculation formula
- identify_fnn_threshold: Verify threshold detection logic
"""

import pytest
import json
import os
import tempfile
from pathlib import Path

import numpy as np

from code.analysis import (
    calculate_metric_error,
    identify_fnn_threshold,
    load_ground_truth_metrics,
    load_noisy_metrics,
    analyze_metric_degradation
)


class TestCalculateMetricError:
    """Tests for calculate_metric_error function"""

    def test_basic_error_calculation(self):
        """Test basic error calculation with known values"""
        computed = 12.0
        ground_truth = 10.0
        expected_error = abs(12.0 - 10.0) / abs(10.0) * 100  # 20%

        error = calculate_metric_error(computed, ground_truth, "test_metric")
        assert abs(error - expected_error) < 1e-6

    def test_zero_computed_value(self):
        """Test error calculation when computed value is zero"""
        computed = 0.0
        ground_truth = 10.0
        expected_error = 100.0  # 100% error

        error = calculate_metric_error(computed, ground_truth, "test_metric")
        assert abs(error - expected_error) < 1e-6

    def test_negative_values(self):
        """Test error calculation with negative values"""
        computed = -12.0
        ground_truth = -10.0
        expected_error = abs(-12.0 - (-10.0)) / abs(-10.0) * 100  # 20%

        error = calculate_metric_error(computed, ground_truth, "test_metric")
        assert abs(error - expected_error) < 1e-6

    def test_near_zero_ground_truth_raises_error(self):
        """Test that near-zero ground truth raises ValueError"""
        computed = 10.0
        ground_truth = 1e-15

        with pytest.raises(ValueError, match="ground_truth_value is too close to zero"):
            calculate_metric_error(computed, ground_truth, "test_metric")

    def test_large_error(self):
        """Test calculation of large errors"""
        computed = 50.0
        ground_truth = 10.0
        expected_error = 400.0  # 400% error

        error = calculate_metric_error(computed, ground_truth, "test_metric")
        assert abs(error - expected_error) < 1e-6


class TestIdentifyFNNThreshold:
    """Tests for identify_fnn_threshold function"""

    def test_threshold_identification(self):
        """Test identification of critical FNN threshold"""
        error_results = [
            {'snr': 0, 'metric_name': 'fnn_rate', 'computed_value': 0.8, 'error_percent': 80.0},
            {'snr': 5, 'metric_name': 'fnn_rate', 'computed_value': 0.6, 'error_percent': 60.0},
            {'snr': 10, 'metric_name': 'fnn_rate', 'computed_value': 0.4, 'error_percent': 40.0},
            {'snr': 15, 'metric_name': 'fnn_rate', 'computed_value': 0.2, 'error_percent': 20.0},
        ]

        threshold = identify_fnn_threshold(error_results, target_fnn_rate=0.5)

        assert threshold is not None
        assert threshold['threshold_snr'] == 5  # First SNR where error > 50%
        assert threshold['metric_name'] == 'fnn_rate'
        assert abs(threshold['error_percent'] - 60.0) < 1e-6

    def test_no_threshold_found(self):
        """Test when no SNR level exceeds threshold"""
        error_results = [
            {'snr': 0, 'metric_name': 'fnn_rate', 'computed_value': 0.3, 'error_percent': 30.0},
            {'snr': 5, 'metric_name': 'fnn_rate', 'computed_value': 0.2, 'error_percent': 20.0},
            {'snr': 10, 'metric_name': 'fnn_rate', 'computed_value': 0.1, 'error_percent': 10.0},
        ]

        threshold = identify_fnn_threshold(error_results, target_fnn_rate=0.5)
        assert threshold is None

    def test_mixed_metrics_filtered(self):
        """Test that only FNN metrics are considered"""
        error_results = [
            {'snr': 0, 'metric_name': 'correlation_dimension', 'computed_value': 2.0, 'error_percent': 10.0},
            {'snr': 5, 'metric_name': 'fnn_rate', 'computed_value': 0.6, 'error_percent': 60.0},
            {'snr': 10, 'metric_name': 'lyapunov_exponent', 'computed_value': 1.5, 'error_percent': 15.0},
        ]

        threshold = identify_fnn_threshold(error_results, target_fnn_rate=0.5)

        assert threshold is not None
        assert threshold['threshold_snr'] == 5

    def test_unsorted_input(self):
        """Test that unsorted input is handled correctly"""
        error_results = [
            {'snr': 15, 'metric_name': 'fnn_rate', 'computed_value': 0.2, 'error_percent': 20.0},
            {'snr': 0, 'metric_name': 'fnn_rate', 'computed_value': 0.8, 'error_percent': 80.0},
            {'snr': 5, 'metric_name': 'fnn_rate', 'computed_value': 0.6, 'error_percent': 60.0},
        ]

        threshold = identify_fnn_threshold(error_results, target_fnn_rate=0.5)

        assert threshold is not None
        assert threshold['threshold_snr'] == 0  # Lowest SNR with error > 50%


class TestLoadGroundTruthMetrics:
    """Tests for load_ground_truth_metrics function"""

    def test_load_single_file(self):
        """Test loading a single ground truth file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a ground truth file
            gt_data = {
                'correlation_dimension': 2.05,
                'lyapunov_exponent': 0.905,
                'fnn_rate': 0.01
            }
            file_path = os.path.join(tmpdir, 'ground_truth_metrics_42.json')
            with open(file_path, 'w') as f:
                json.dump(gt_data, f)

            result = load_ground_truth_metrics(tmpdir)

            assert '42' in result
            assert abs(result['42']['correlation_dimension'] - 2.05) < 1e-6

    def test_no_files_raises_error(self):
        """Test that missing files raise FileNotFoundError"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(FileNotFoundError):
                load_ground_truth_metrics(tmpdir)


class TestLoadNoisyMetrics:
    """Tests for load_noisy_metrics function"""

    def test_load_multiple_files(self):
        """Test loading multiple noisy metric files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple metric files
            for i, snr in enumerate([0, 10, 20]):
                metric_data = {
                    'snr': snr,
                    'noise_type': 'gaussian',
                    'correlation_dimension': 2.0 + i * 0.1,
                    'lyapunov_exponent': 0.9 + i * 0.05,
                    'fnn_rate': 0.01 + i * 0.1
                }
                file_path = os.path.join(tmpdir, f'metric_snr_{snr}.json')
                with open(file_path, 'w') as f:
                    json.dump(metric_data, f)

            result = load_noisy_metrics(tmpdir)

            assert len(result) == 3
            snrs = [r['snr'] for r in result]
            assert 0 in snrs
            assert 10 in snrs
            assert 20 in snrs

    def test_invalid_json_skipped(self):
        """Test that invalid JSON files are skipped"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a valid file
            valid_data = {'snr': 10, 'metric': 'value'}
            valid_path = os.path.join(tmpdir, 'valid.json')
            with open(valid_path, 'w') as f:
                json.dump(valid_data, f)

            # Create an invalid file
            invalid_path = os.path.join(tmpdir, 'invalid.json')
            with open(invalid_path, 'w') as f:
                f.write("not valid json")

            result = load_noisy_metrics(tmpdir)

            assert len(result) == 1
            assert result[0]['snr'] == 10


class TestAnalyzeMetricDegradation:
    """Tests for analyze_metric_degradation function"""

    def test_basic_degradation_analysis(self):
        """Test basic metric degradation analysis"""
        ground_truth = {
            '42': {
                'correlation_dimension': 2.05,
                'lyapunov_exponent': 0.905,
                'fnn_rate': 0.01
            }
        }

        noisy_metrics = [
            {
                'snr': 10,
                'noise_type': 'gaussian',
                'system_type': 'lorenz',
                'seed': 42,
                'correlation_dimension': 2.15,
                'lyapunov_exponent': 0.95,
                'fnn_rate': 0.15
            }
        ]

        errors = analyze_metric_degradation(ground_truth, noisy_metrics)

        assert len(errors) == 3  # Three metrics
        error_dict = {e['metric_name']: e for e in errors}

        # Check correlation dimension error
        cd_error = error_dict['correlation_dimension']['error_percent']
        expected_cd_error = abs(2.15 - 2.05) / 2.05 * 100
        assert abs(cd_error - expected_cd_error) < 1e-4

        # Check lyapunov exponent error
        le_error = error_dict['lyapunov_exponent']['error_percent']
        expected_le_error = abs(0.95 - 0.905) / 0.905 * 100
        assert abs(le_error - expected_le_error) < 1e-4

    def test_missing_ground_truth_warns(self):
        """Test that missing ground truth for a metric is handled"""
        ground_truth = {
            '42': {
                'correlation_dimension': 2.05,
                'lyapunov_exponent': 0.905
                # fnn_rate missing
            }
        }

        noisy_metrics = [
            {
                'snr': 10,
                'noise_type': 'gaussian',
                'system_type': 'lorenz',
                'seed': 42,
                'correlation_dimension': 2.15,
                'lyapunov_exponent': 0.95,
                'fnn_rate': 0.15
            }
        ]

        errors = analyze_metric_degradation(ground_truth, noisy_metrics)

        # Only 2 errors expected (fnn_rate should be skipped)
        assert len(errors) == 2
        metric_names = [e['metric_name'] for e in errors]
        assert 'correlation_dimension' in metric_names
        assert 'lyapunov_exponent' in metric_names
        assert 'fnn_rate' not in metric_names