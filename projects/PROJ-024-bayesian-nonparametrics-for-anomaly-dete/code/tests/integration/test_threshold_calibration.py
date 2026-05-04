"""
Integration test for unlabeled data threshold calibration.

This test verifies that the threshold calibration mechanism works
correctly on unlabeled data and produces reasonable anomaly rates.

Independent Test Scenario (per spec.md):
- Can be fully tested by running the model on unlabeled data
- Verifying that the adaptive threshold produces reasonable 
  anomaly rates based on statistical properties of the scores
"""
import os
import sys
import pytest
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.threshold import (
    ThresholdCalibrator,
    ThresholdConfig,
    ThresholdCalibrationResult,
    compute_adaptive_threshold,
    validate_anomaly_rate,
    save_calibration_result,
    load_calibration_result
)
from data.synthetic_generator import generate_synthetic_timeseries, AnomalyConfig, SignalConfig


class TestThresholdCalibrationUnlabeledData:
    """
    Integration tests for threshold calibration on unlabeled data.
    
    These tests verify that threshold calibration works correctly
    without requiring labeled ground truth data.
    """

    @pytest.fixture
    def synthetic_scores(self):
        """Generate synthetic anomaly scores for testing."""
        np.random.seed(42)
        n_observations = 1000
        
        # Create normal scores with injected anomalies
        normal_scores = np.random.normal(loc=0.0, scale=1.0, size=int(0.9 * n_observations))
        anomaly_scores = np.random.normal(loc=3.0, scale=0.5, size=int(0.1 * n_observations))
        scores = np.concatenate([normal_scores, anomaly_scores])
        
        # Shuffle to simulate real-world unlabeled data
        np.random.shuffle(scores)
        
        return scores

    @pytest.fixture
    def default_calibrator(self):
        """Create a calibrator with default configuration."""
        return ThresholdCalibrator()

    @pytest.fixture
    def strict_calibrator(self):
        """Create a calibrator with strict anomaly rate bounds."""
        config = ThresholdConfig(
            percentile=95.0,
            min_anomaly_rate=0.02,
            max_anomaly_rate=0.08,
            min_samples=50
        )
        return ThresholdCalibrator(config)

    def test_calibrate_on_unlabeled_data(self, synthetic_scores, default_calibrator):
        """
        Test that calibration works on unlabeled data.
        
        Verifies that the calibrator can compute a threshold
        without requiring labeled ground truth.
        """
        # Perform calibration
        result = default_calibrator.calibrate(synthetic_scores)
        
        # Verify result structure
        assert isinstance(result, ThresholdCalibrationResult)
        assert result.threshold > 0
        assert 0 <= result.anomaly_rate <= 1
        assert result.num_observations == len(synthetic_scores)
        assert result.calibrated_at is not None
        
        # Verify percentiles are computed
        assert 'p25' in result.score_percentiles
        assert 'p50' in result.score_percentiles
        assert 'p75' in result.score_percentiles
        assert 'p95' in result.score_percentiles
        assert 'mean' in result.score_percentiles
        assert 'std' in result.score_percentiles

    def test_threshold_produces_reasonable_anomaly_rate(self, synthetic_scores, default_calibrator):
        """
        Test that the calibrated threshold produces reasonable anomaly rates.
        
        Verifies that the anomaly rate falls within expected bounds
        (typically 1-10% for anomaly detection scenarios).
        """
        result = default_calibrator.calibrate(synthetic_scores)
        
        # Verify anomaly rate is within configured bounds
        assert default_calibrator.config.min_anomaly_rate <= result.anomaly_rate <= \
               default_calibrator.config.max_anomaly_rate

    def test_calibration_result_validation(self, synthetic_scores, default_calibrator):
        """
        Test that validation correctly identifies when anomaly rates are acceptable.
        """
        result = default_calibrator.calibrate(synthetic_scores)
        
        # Validation should pass if rate is within bounds
        assert result.validation_passed == (
            default_calibrator.config.min_anomaly_rate <= result.anomaly_rate <=
            default_calibrator.config.max_anomaly_rate
        )

    def test_calibrator_state_persistence(self, synthetic_scores, default_calibrator):
        """
        Test that calibrator maintains state after calibration.
        """
        # First calibration
        result1 = default_calibrator.calibrate(synthetic_scores[:500])
        
        # Verify state is stored
        assert default_calibrator._calibrated is True
        assert default_calibrator._threshold is not None
        
        # Get threshold via public method
        threshold = default_calibrator.get_threshold()
        assert threshold == result1.threshold

    def test_validation_with_new_scores(self, synthetic_scores, default_calibrator):
        """
        Test that threshold validation works on new score data.
        """
        # Calibrate on first half
        default_calibrator.calibrate(synthetic_scores[:500])
        
        # Validate on second half
        is_valid = default_calibrator.validate_threshold(synthetic_scores[500:])
        
        # Should be a boolean
        assert isinstance(is_valid, bool)

    def test_adaptive_threshold_function(self, synthetic_scores):
        """
        Test the convenience compute_adaptive_threshold function.
        """
        result = compute_adaptive_threshold(
            synthetic_scores,
            percentile=95.0,
            min_rate=0.01,
            max_rate=0.10
        )
        
        assert isinstance(result, ThresholdCalibrationResult)
        assert result.threshold > 0
        assert 0 <= result.anomaly_rate <= 1

    def test_validate_anomaly_rate_function(self, synthetic_scores):
        """
        Test the validate_anomaly_rate convenience function.
        """
        threshold = np.percentile(synthetic_scores, 95)
        
        passed, rate = validate_anomaly_rate(
            synthetic_scores,
            threshold,
            min_rate=0.01,
            max_rate=0.10
        )
        
        assert isinstance(passed, bool)
        assert 0 <= rate <= 1

    def test_save_and_load_calibration_result(self, synthetic_scores, tmp_path):
        """
        Test serialization and deserialization of calibration results.
        """
        # Calibrate and save
        calibrator = ThresholdCalibrator()
        result = calibrator.calibrate(synthetic_scores)
        
        output_path = tmp_path / "calibration_result.json"
        save_calibration_result(result, output_path)
        
        # Verify file was created
        assert output_path.exists()
        
        # Load and verify
        loaded_result = load_calibration_result(output_path)
        
        assert loaded_result.threshold == result.threshold
        assert loaded_result.anomaly_rate == result.anomaly_rate
        assert loaded_result.num_observations == result.num_observations

    def test_insufficient_samples_raises_error(self, default_calibrator):
        """
        Test that calibration fails gracefully with insufficient samples.
        """
        small_scores = np.random.normal(loc=0.0, scale=1.0, size=50)
        
        with pytest.raises(ValueError) as exc_info:
            default_calibrator.calibrate(small_scores)
        
        assert "Insufficient samples" in str(exc_info.value)

    def test_uncalibrated_threshold_raises_error(self, default_calibrator):
        """
        Test that getting threshold before calibration raises error.
        """
        with pytest.raises(RuntimeError) as exc_info:
            default_calibrator.get_threshold()
        
        assert "not yet calibrated" in str(exc_info.value).lower()

    def test_uncalibrated_validation_raises_error(self, default_calibrator, synthetic_scores):
        """
        Test that validation before calibration raises error.
        """
        with pytest.raises(RuntimeError) as exc_info:
            default_calibrator.validate_threshold(synthetic_scores)
        
        assert "not yet calibrated" in str(exc_info.value).lower()

    def test_manual_threshold_update(self, default_calibrator):
        """
        Test that threshold can be manually updated.
        """
        # Set a manual threshold
        new_threshold = 2.5
        default_calibrator.update_threshold(new_threshold)
        
        # Verify update
        assert default_calibrator.get_threshold() == new_threshold
        assert default_calibrator._calibrated is True

    def test_decision_boundary_access(self, synthetic_scores, default_calibrator):
        """
        Test that decision boundary can be accessed.
        """
        default_calibrator.calibrate(synthetic_scores)
        
        boundary = default_calibrator.get_decision_boundary()
        assert boundary == default_calibrator.get_threshold()

    def test_expected_bounds_computation(self, default_calibrator):
        """
        Test that expected anomaly rate bounds can be computed.
        """
        bounds = default_calibrator.compute_expected_bounds()
        
        assert isinstance(bounds, tuple)
        assert len(bounds) == 2
        assert bounds[0] == default_calibrator.config.min_anomaly_rate
        assert bounds[1] == default_calibrator.config.max_anomaly_rate

    def test_calibration_result_serialization(self, synthetic_scores, default_calibrator):
        """
        Test that calibration result can be converted to dictionary.
        """
        result = default_calibrator.calibrate(synthetic_scores)
        result_dict = result.to_dict()
        
        # Verify all expected keys are present
        expected_keys = [
            'threshold', 'anomaly_rate', 'score_percentiles',
            'calibrated_at', 'num_observations', 'num_anomalies_detected',
            'decision_boundary', 'expected_anomaly_bounds', 'validation_passed'
        ]
        
        for key in expected_keys:
            assert key in result_dict

    def test_percentile_threshold_computation(self, synthetic_scores):
        """
        Test that percentile-based threshold is computed correctly.
        """
        expected_95th = np.percentile(synthetic_scores, 95)
        
        result = compute_adaptive_threshold(synthetic_scores, percentile=95.0)
        
        # Should be very close to actual 95th percentile
        assert abs(result.threshold - expected_95th) < 0.01

    def test_anomaly_detection_with_calibrated_threshold(self, synthetic_scores, default_calibrator):
        """
        Test that calibrated threshold correctly identifies anomalies.
        """
        # Calibrate
        result = default_calibrator.calibrate(synthetic_scores)
        
        # Apply threshold to get anomalies
        anomaly_mask = synthetic_scores >= result.threshold
        detected_anomalies = np.sum(anomaly_mask)
        
        # Verify count matches result
        assert detected_anomalies == result.num_anomalies_detected

    def test_score_percentiles_accuracy(self, synthetic_scores, default_calibrator):
        """
        Test that computed percentiles match numpy calculations.
        """
        result = default_calibrator.calibrate(synthetic_scores)
        
        # Verify key percentiles
        assert abs(result.score_percentiles['p25'] - np.percentile(synthetic_scores, 25)) < 0.01
        assert abs(result.score_percentiles['p50'] - np.percentile(synthetic_scores, 50)) < 0.01
        assert abs(result.score_percentiles['p75'] - np.percentile(synthetic_scores, 75)) < 0.01
        assert abs(result.score_percentiles['p95'] - np.percentile(synthetic_scores, 95)) < 0.01

    def test_config_parameters_affect_calibration(self, synthetic_scores):
        """
        Test that configuration parameters affect calibration results.
        """
        # Calibrator with 90th percentile
        calibrator_90 = ThresholdCalibrator(
            ThresholdConfig(percentile=90.0, min_samples=50)
        )
        result_90 = calibrator_90.calibrate(synthetic_scores)
        
        # Calibrator with 99th percentile
        calibrator_99 = ThresholdCalibrator(
            ThresholdConfig(percentile=99.0, min_samples=50)
        )
        result_99 = calibrator_99.calibrate(synthetic_scores)
        
        # Higher percentile should give higher threshold
        assert result_99.threshold > result_90.threshold
        
        # Higher percentile should give lower anomaly rate
        assert result_99.anomaly_rate < result_90.anomaly_rate


class TestThresholdCalibrationWithRealisticData:
    """
    Integration tests using more realistic synthetic time series data.
    """

    @pytest.fixture
    def realistic_scores(self):
        """Generate realistic anomaly scores from synthetic time series."""
        # Generate synthetic time series with anomalies
        np.random.seed(123)
        
        signal_config = SignalConfig(
            signal_type='sine',
            frequency=0.1,
            amplitude=1.0,
            noise_std=0.1
        )
        
        anomaly_config = AnomalyConfig(
            anomaly_rate=0.05,
            anomaly_magnitude=3.0
        )
        
        # Generate synthetic dataset
        data = generate_synthetic_timeseries(
            signal_config=signal_config,
            anomaly_config=anomaly_config,
            n_points=1000
        )
        
        # Simulate anomaly scores (in practice, these would come from DPGMM)
        # Normal points: low scores, Anomalies: high scores
        scores = np.abs(data['values'] + np.random.normal(0, 0.1, len(data['values'])))
        
        return scores

    def test_calibration_on_realistic_scores(self, realistic_scores):
        """
        Test calibration on scores from realistic time series.
        """
        calibrator = ThresholdCalibrator()
        result = calibrator.calibrate(realistic_scores)
        
        assert result.threshold > 0
        assert 0 <= result.anomaly_rate <= 1
        assert result.num_observations == len(realistic_scores)

    def test_stability_across_multiple_calibrations(self, realistic_scores):
        """
        Test that calibration is stable across multiple runs.
        """
        results = []
        
        for _ in range(3):
            calibrator = ThresholdCalibrator()
            result = calibrator.calibrate(realistic_scores)
            results.append(result.threshold)
        
        # Thresholds should be very similar (same data, deterministic)
        assert max(results) - min(results) < 0.01


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
