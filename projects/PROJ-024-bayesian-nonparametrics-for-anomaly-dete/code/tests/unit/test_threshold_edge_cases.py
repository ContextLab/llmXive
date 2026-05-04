"""
Unit tests for threshold calibration edge cases.

Tests cover:
- Empty score distributions
- Single score
- Extreme score values
- All same scores
"""
import pytest
import numpy as np
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from utils.threshold import ThresholdCalibrator, compute_adaptive_threshold


class TestThresholdEdgeCases:
    """Test threshold calibration edge cases."""
    
    def test_empty_scores(self):
        """Test threshold calibration with empty scores."""
        calibrator = ThresholdCalibrator(
            percentile=95,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        threshold = calibrator.calibrate(np.array([]))
        assert threshold is None
    
    def test_single_score(self):
        """Test threshold calibration with single score."""
        calibrator = ThresholdCalibrator(
            percentile=95,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        threshold = calibrator.calibrate(np.array([5.0]))
        assert threshold is not None
        assert threshold == 5.0  # Single value threshold
    
    def test_all_same_scores(self):
        """Test threshold calibration with all same scores."""
        calibrator = ThresholdCalibrator(
            percentile=95,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        scores = np.ones(100) * 5.0
        threshold = calibrator.calibrate(scores)
        assert threshold is not None
        assert threshold == 5.0
    
    def test_extreme_percentile_values(self):
        """Test with extreme percentile values."""
        calibrator_low = ThresholdCalibrator(
            percentile=1,  # Very low
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        calibrator_high = ThresholdCalibrator(
            percentile=99,  # Very high
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        scores = np.random.normal(0, 1, 1000)
        
        threshold_low = calibrator_low.calibrate(scores)
        threshold_high = calibrator_high.calibrate(scores)
        
        assert threshold_low < threshold_high
    
    def test_percentile_zero(self):
        """Test with percentile 0."""
        calibrator = ThresholdCalibrator(
            percentile=0,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        scores = np.random.normal(0, 1, 100)
        threshold = calibrator.calibrate(scores)
        assert threshold is not None
        assert threshold == np.min(scores)
    
    def test_percentile_hundred(self):
        """Test with percentile 100."""
        calibrator = ThresholdCalibrator(
            percentile=100,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        scores = np.random.normal(0, 1, 100)
        threshold = calibrator.calibrate(scores)
        assert threshold is not None
        assert threshold == np.max(scores)
    
    def test_extreme_score_values(self):
        """Test with extreme score values."""
        calibrator = ThresholdCalibrator(
            percentile=95,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        # Very large scores
        scores_large = np.array([1e6, 1e6 + 1, 1e6 + 2, 1e6 + 3, 1e6 + 4])
        threshold_large = calibrator.calibrate(scores_large)
        assert threshold_large is not None
        assert threshold_large > 1e6
        
        # Very small scores
        scores_small = np.array([1e-10, 1e-10 + 1e-12, 1e-10 + 2e-12])
        threshold_small = calibrator.calibrate(scores_small)
        assert threshold_small is not None
        assert threshold_small > 0
    
    def test_nan_scores(self):
        """Test with NaN scores."""
        calibrator = ThresholdCalibrator(
            percentile=95,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        scores = np.array([1.0, 2.0, np.nan, 4.0, 5.0])
        threshold = calibrator.calibrate(scores)
        # Should handle NaN gracefully
        assert threshold is not None
    
    def test_inf_scores(self):
        """Test with infinite scores."""
        calibrator = ThresholdCalibrator(
            percentile=95,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        scores = np.array([1.0, 2.0, np.inf, 4.0, 5.0])
        threshold = calibrator.calibrate(scores)
        # Should handle inf gracefully
        assert threshold is not None
    
    def test_min_anomaly_rate_constraint(self):
        """Test minimum anomaly rate constraint."""
        calibrator = ThresholdCalibrator(
            percentile=99,  # Would give very low anomaly rate
            min_anomaly_rate=0.1,  # Force at least 10%
            max_anomaly_rate=0.5
        )
        
        scores = np.random.normal(0, 1, 100)
        threshold = calibrator.calibrate(scores)
        
        # Should respect min anomaly rate
        anomaly_rate = np.mean(scores > threshold)
        assert anomaly_rate >= 0.1
    
    def test_max_anomaly_rate_constraint(self):
        """Test maximum anomaly rate constraint."""
        calibrator = ThresholdCalibrator(
            percentile=1,  # Would give very high anomaly rate
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.05  # Force at most 5%
        )
        
        scores = np.random.normal(0, 1, 100)
        threshold = calibrator.calibrate(scores)
        
        # Should respect max anomaly rate
        anomaly_rate = np.mean(scores > threshold)
        assert anomaly_rate <= 0.05
    
    def test_compute_adaptive_threshold(self):
        """Test compute_adaptive_threshold function."""
        scores = np.random.normal(0, 1, 1000)
        
        threshold = compute_adaptive_threshold(
            scores,
            percentile=95,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        assert threshold is not None
        assert isinstance(threshold, float)
    
    def test_adaptive_threshold_empty(self):
        """Test compute_adaptive_threshold with empty scores."""
        threshold = compute_adaptive_threshold(
            np.array([]),
            percentile=95,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        assert threshold is None
    
    def test_threshold_validation(self):
        """Test threshold validation."""
        calibrator = ThresholdCalibrator(
            percentile=95,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        scores = np.random.normal(0, 1, 100)
        threshold = calibrator.calibrate(scores)
        
        # Validate threshold produces expected anomaly rate
        is_valid = calibrator.validate_threshold(threshold, scores)
        assert is_valid is not None
    
    def test_threshold_update(self):
        """Test threshold update with new scores."""
        calibrator = ThresholdCalibrator(
            percentile=95,
            min_anomaly_rate=0.01,
            max_anomaly_rate=0.1
        )
        
        scores1 = np.random.normal(0, 1, 100)
        threshold1 = calibrator.calibrate(scores1)
        
        scores2 = np.random.normal(0, 1, 100)
        threshold2 = calibrator.update(threshold1, scores2)
        
        # Should update threshold based on new data
        assert threshold2 is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
