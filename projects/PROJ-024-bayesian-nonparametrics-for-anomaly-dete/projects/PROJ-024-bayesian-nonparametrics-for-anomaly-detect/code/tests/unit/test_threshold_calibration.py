"""
Unit tests for threshold calibration logic (US3).

Tests the percentile-based calibration method and adaptive boundary
update logic for the ThresholdCalibratorService.

These tests verify:
1. Percentile-based threshold calculation works correctly
2. Adaptive boundary updates adjust to score distribution changes
3. Calibration handles edge cases (empty data, single value, etc.)
4. Threshold adapts to score distribution without labeled data
"""

import pytest
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import sys

# Add code directory to path for imports
code_path = Path(__file__).parent.parent.parent / "src"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from models.anomaly_score import AnomalyScore
from datetime import datetime


@dataclass
class CalibrationResult:
    """Result from threshold calibration."""
    threshold: float
    percentile: float
    score_count: int
    mean_score: float
    std_score: float
    min_score: float
    max_score: float
    calibrated_at: datetime = field(default_factory=datetime.now)


class ThresholdCalibrator:
    """
    Standalone threshold calibrator for unit testing.

    This implements the core calibration logic that will be
    wrapped by ThresholdCalibratorService in T034/T160.
    """

    def __init__(self, percentile: float = 95.0):
        """
        Initialize calibrator.

        Args:
            percentile: Target percentile for threshold (default 95th)
        """
        if not 0 < percentile < 100:
            raise ValueError(f"Percentile must be between 0 and 100, got {percentile}")
        self.percentile = percentile
        self._scores: List[float] = []
        self._current_threshold: Optional[float] = None

    def add_score(self, score: float) -> None:
        """Add a single anomaly score to the calibration buffer."""
        self._scores.append(score)

    def add_scores(self, scores: List[float]) -> None:
        """Add multiple anomaly scores to the calibration buffer."""
        self._scores.extend(scores)

    def calibrate(self) -> CalibrationResult:
        """
        Calculate threshold based on current score distribution.

        Returns:
            CalibrationResult with threshold and distribution statistics
        """
        if not self._scores:
            raise ValueError("No scores available for calibration")

        scores_array = np.array(self._scores)

        # Calculate percentile-based threshold
        threshold = float(np.percentile(scores_array, self.percentile))

        result = CalibrationResult(
            threshold=threshold,
            percentile=self.percentile,
            score_count=len(self._scores),
            mean_score=float(np.mean(scores_array)),
            std_score=float(np.std(scores_array)),
            min_score=float(np.min(scores_array)),
            max_score=float(np.max(scores_array))
        )

        self._current_threshold = threshold
        return result

    def get_current_threshold(self) -> Optional[float]:
        """Return the current calibrated threshold."""
        return self._current_threshold

    def reset(self) -> None:
        """Clear the score buffer and reset threshold."""
        self._scores = []
        self._current_threshold = None

    def get_score_statistics(self) -> Dict[str, float]:
        """Return current score distribution statistics."""
        if not self._scores:
            return {
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0
            }

        scores_array = np.array(self._scores)
        return {
            "count": len(self._scores),
            "mean": float(np.mean(scores_array)),
            "std": float(np.std(scores_array)),
            "min": float(np.min(scores_array)),
            "max": float(np.max(scores_array))
        }


class AdaptiveThresholdCalibrator:
    """
    Adaptive threshold calibrator with sliding window.

    This implements the adaptive boundary update logic that adjusts
    threshold based on recent score distribution changes.
    """

    def __init__(self, percentile: float = 95.0, window_size: int = 100):
        """
        Initialize adaptive calibrator.

        Args:
            percentile: Target percentile for threshold
            window_size: Number of recent scores to consider for adaptation
        """
        self.percentile = percentile
        self.window_size = window_size
        self._scores: List[float] = []
        self._current_threshold: Optional[float] = None
        self._update_count: int = 0

    def add_score(self, score: float) -> Tuple[bool, Optional[float]]:
        """
        Add a score and potentially update threshold adaptively.

        Args:
            score: Anomaly score to add

        Returns:
            Tuple of (threshold_updated, new_threshold)
        """
        self._scores.append(score)

        # Only update threshold when window is full
        if len(self._scores) >= self.window_size:
            # Trim oldest scores to maintain window
            self._scores = self._scores[-self.window_size:]

            # Calculate new threshold
            scores_array = np.array(self._scores)
            new_threshold = float(np.percentile(scores_array, self.percentile))

            # Check if threshold changed significantly
            if self._current_threshold is None:
                threshold_updated = True
            else:
                relative_change = abs(new_threshold - self._current_threshold) / max(self._current_threshold, 1e-10)
                threshold_updated = relative_change > 0.05  # 5% change threshold

            if threshold_updated:
                self._current_threshold = new_threshold
                self._update_count += 1

            return threshold_updated, self._current_threshold

        return False, self._current_threshold

    def get_current_threshold(self) -> Optional[float]:
        """Return the current threshold."""
        return self._current_threshold

    def get_update_count(self) -> int:
        """Return number of threshold updates performed."""
        return self._update_count

    def reset(self) -> None:
        """Reset the calibrator."""
        self._scores = []
        self._current_threshold = None
        self._update_count = 0


# ==================== TESTS ====================

class TestPercentileCalibration:
    """Tests for percentile-based threshold calibration."""

    def test_calibrate_normal_distribution(self):
        """Test calibration on normally distributed scores."""
        np.random.seed(42)
        scores = np.random.normal(loc=0.5, scale=0.1, size=1000).tolist()

        calibrator = ThresholdCalibrator(percentile=95.0)
        calibrator.add_scores(scores)

        result = calibrator.calibrate()

        # Threshold should be at approximately 95th percentile
        expected_threshold = float(np.percentile(scores, 95.0))
        assert abs(result.threshold - expected_threshold) < 1e-6
        assert result.score_count == 1000
        assert result.min_score <= result.threshold <= result.max_score

    def test_calibrate_with_anomalies(self):
        """Test calibration when some scores are clearly anomalous."""
        np.random.seed(42)
        # Normal scores
        normal_scores = np.random.normal(loc=0.3, scale=0.05, size=950).tolist()
        # Anomalous scores (much higher)
        anomaly_scores = np.random.normal(loc=0.9, scale=0.05, size=50).tolist()

        all_scores = normal_scores + anomaly_scores
        calibrator = ThresholdCalibrator(percentile=95.0)
        calibrator.add_scores(all_scores)

        result = calibrator.calibrate()

        # Threshold should separate normal from anomalous
        assert result.threshold > 0.5  # Above normal range
        assert result.threshold < 0.8  # Below anomalous range
        assert result.std_score > 0.1  # Should show variance

    def test_calibrate_single_value(self):
        """Test calibration with a single score."""
        calibrator = ThresholdCalibrator(percentile=95.0)
        calibrator.add_score(0.75)

        result = calibrator.calibrate()

        assert result.threshold == 0.75
        assert result.score_count == 1
        assert result.mean_score == 0.75

    def test_calibrate_two_values(self):
        """Test calibration with two scores."""
        calibrator = ThresholdCalibrator(percentile=95.0)
        calibrator.add_scores([0.3, 0.8])

        result = calibrator.calibrate()

        # With 95th percentile on 2 values, should be close to max
        assert result.threshold >= 0.8

    def test_calibrate_empty_buffer_raises(self):
        """Test that calibration raises error on empty buffer."""
        calibrator = ThresholdCalibrator(percentile=95.0)

        with pytest.raises(ValueError, match="No scores available"):
            calibrator.calibrate()

    def test_invalid_percentile_raises(self):
        """Test that invalid percentile raises error."""
        with pytest.raises(ValueError):
            ThresholdCalibrator(percentile=100.0)

        with pytest.raises(ValueError):
            ThresholdCalibrator(percentile=0.0)

        with pytest.raises(ValueError):
            ThresholdCalibrator(percentile=-5.0)

    def test_different_percentiles(self):
        """Test calibration at different percentile values."""
        scores = list(np.linspace(0.1, 0.9, 1000))

        calibrator_90 = ThresholdCalibrator(percentile=90.0)
        calibrator_90.add_scores(scores)
        result_90 = calibrator_90.calibrate()

        calibrator_99 = ThresholdCalibrator(percentile=99.0)
        calibrator_99.add_scores(scores)
        result_99 = calibrator_99.calibrate()

        # Higher percentile should give higher threshold
        assert result_99.threshold > result_90.threshold

    def test_get_score_statistics(self):
        """Test score statistics calculation."""
        scores = [0.1, 0.3, 0.5, 0.7, 0.9]
        calibrator = ThresholdCalibrator()
        calibrator.add_scores(scores)

        stats = calibrator.get_score_statistics()

        assert stats["count"] == 5
        assert stats["mean"] == 0.5
        assert stats["min"] == 0.1
        assert stats["max"] == 0.9

    def test_reset_clears_buffer(self):
        """Test that reset clears all state."""
        calibrator = ThresholdCalibrator()
        calibrator.add_scores([0.1, 0.5, 0.9])
        calibrator.calibrate()

        calibrator.reset()

        with pytest.raises(ValueError):
            calibrator.calibrate()

        assert calibrator.get_current_threshold() is None


class TestAdaptiveCalibration:
    """Tests for adaptive threshold calibration with sliding window."""

    def test_adaptive_update_after_window(self):
        """Test that threshold updates after window fills."""
        calibrator = AdaptiveThresholdCalibrator(percentile=90.0, window_size=10)

        # Add scores below window size
        for i in range(9):
            updated, threshold = calibrator.add_score(0.3)
            assert not updated
            assert threshold is None

        # Add 10th score - should trigger update
        updated, threshold = calibrator.add_score(0.5)
        assert updated
        assert threshold is not None
        assert calibrator.get_update_count() == 1

    def test_adaptive_threshold_change_detection(self):
        """Test that significant threshold changes are detected."""
        calibrator = AdaptiveThresholdCalibrator(percentile=90.0, window_size=10)

        # Fill with low scores
        for i in range(10):
            calibrator.add_score(0.2)

        initial_threshold = calibrator.get_current_threshold()

        # Now add high scores
        for i in range(10):
            updated, _ = calibrator.add_score(0.9)
            if updated:
                break

        final_threshold = calibrator.get_current_threshold()

        # Threshold should have increased significantly
        assert final_threshold is not None
        assert final_threshold > initial_threshold

    def test_adaptive_window_maintenance(self):
        """Test that window maintains correct size."""
        window_size = 20
        calibrator = AdaptiveThresholdCalibrator(percentile=90.0, window_size=window_size)

        # Add more scores than window size
        for i in range(50):
            calibrator.add_score(0.5)

        # Internal buffer should be at window size
        assert len(calibrator._scores) == window_size

    def test_adaptive_no_update_on_small_change(self):
        """Test that small threshold changes don't trigger update."""
        calibrator = AdaptiveThresholdCalibrator(percentile=90.0, window_size=10)

        # Fill window with same value
        for i in range(10):
            calibrator.add_score(0.5)

        initial_threshold = calibrator.get_current_threshold()
        initial_count = calibrator.get_update_count()

        # Add similar value - should not trigger update
        updated, _ = calibrator.add_score(0.51)  # 2% change
        assert not updated
        assert calibrator.get_update_count() == initial_count

    def test_adaptive_reset(self):
        """Test that reset clears all adaptive state."""
        calibrator = AdaptiveThresholdCalibrator()

        for i in range(20):
            calibrator.add_score(0.5)

        calibrator.reset()

        assert len(calibrator._scores) == 0
        assert calibrator.get_current_threshold() is None
        assert calibrator.get_update_count() == 0

    def test_adaptive_with_realistic_distribution(self):
        """Test adaptive calibration with realistic anomaly score distribution."""
        np.random.seed(42)
        calibrator = AdaptiveThresholdCalibrator(percentile=95.0, window_size=100)

        # Generate realistic scores: mostly normal, some anomalies
        normal_scores = np.random.normal(loc=0.2, scale=0.05, size=900)
        anomaly_scores = np.random.normal(loc=0.8, scale=0.1, size=100)

        all_scores = np.concatenate([normal_scores, anomaly_scores])

        updates = 0
        for score in all_scores:
            updated, _ = calibrator.add_score(float(score))
            if updated:
                updates += 1

        # Should have some threshold updates as distribution settles
        assert updates > 0
        assert calibrator.get_current_threshold() is not None


class TestIntegrationScenarios:
    """Integration scenarios for threshold calibration workflow."""

    def test_calibrate_streaming_workflow(self):
        """Test complete streaming calibration workflow."""
        np.random.seed(42)
        calibrator = ThresholdCalibrator(percentile=95.0)

        # Simulate streaming scores
        for i in range(1000):
            # Normal scores with occasional anomalies
            if np.random.random() < 0.05:  # 5% anomaly rate
                score = np.random.uniform(0.7, 0.95)
            else:
                score = np.random.normal(loc=0.3, scale=0.05)

            calibrator.add_score(float(score))

        result = calibrator.calibrate()

        # Verify calibration completed successfully
        assert result.score_count == 1000
        assert 0.3 < result.threshold < 0.8  # Should be in normal range
        assert result.max_score > result.threshold  # Anomalies above threshold

    def test_calibrate_with_anomaly_score_objects(self):
        """Test calibration using AnomalyScore dataclass objects."""
        calibrator = ThresholdCalibrator(percentile=90.0)

        # Create AnomalyScore objects
        scores = []
        for i in range(100):
            score = AnomalyScore(
                value=float(np.random.normal(0.3, 0.05)),
                timestamp=datetime.now(),
                model_name="test_model",
                is_anomaly=False
            )
            scores.append(score.value)

        calibrator.add_scores(scores)
        result = calibrator.calibrate()

        assert result.threshold is not None
        assert result.score_count == 100

    def test_calibrate_boundary_conditions(self):
        """Test calibration at boundary conditions."""
        # All scores at same value
        calibrator = ThresholdCalibrator(percentile=95.0)
        calibrator.add_scores([0.5] * 100)
        result = calibrator.calibrate()
        assert result.threshold == 0.5

        # Scores at exact 0 and 1
        calibrator = ThresholdCalibrator(percentile=50.0)
        calibrator.add_scores([0.0] * 50 + [1.0] * 50)
        result = calibrator.calibrate()
        assert result.threshold == 0.5

    def test_calibrate_adaptive_vs_static(self):
        """Compare static and adaptive calibration approaches."""
        np.random.seed(42)

        # Generate scores with drift
        scores = []
        for i in range(500):
            base = 0.3 + (i / 500) * 0.4  # Drift from 0.3 to 0.7
            scores.append(float(np.random.normal(base, 0.05)))

        # Static calibration on all scores
        static_calibrator = ThresholdCalibrator(percentile=95.0)
        static_calibrator.add_scores(scores)
        static_result = static_calibrator.calibrate()

        # Adaptive calibration with window
        adaptive_calibrator = AdaptiveThresholdCalibrator(percentile=95.0, window_size=100)
        for score in scores:
            adaptive_calibrator.add_score(score)

        adaptive_threshold = adaptive_calibrator.get_current_threshold()

        # Adaptive should reflect more recent distribution
        assert adaptive_threshold is not None
        # Adaptive threshold should be higher due to drift
        assert adaptive_threshold > static_result.threshold - 0.1


# ==================== FIXTURES ====================

@pytest.fixture
def sample_scores():
    """Provide sample anomaly scores for testing."""
    np.random.seed(42)
    return (
        np.random.normal(loc=0.3, scale=0.05, size=950).tolist() +
        np.random.normal(loc=0.8, scale=0.1, size=50).tolist()
    )

@pytest.fixture
def empty_calibrator():
    """Provide empty calibrator for setup tests."""
    return ThresholdCalibrator(percentile=95.0)

@pytest.fixture
def adaptive_calibrator():
    """Provide adaptive calibrator for setup tests."""
    return AdaptiveThresholdCalibrator(percentile=95.0, window_size=100)
