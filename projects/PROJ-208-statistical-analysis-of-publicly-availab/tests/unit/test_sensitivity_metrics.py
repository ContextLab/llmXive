"""
Unit tests for sensitivity analysis metrics calculation.
"""
import numpy as np
import pytest
from pathlib import Path
import sys

# Add code directory to path if needed for imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from diagnostics.sensitivity_analysis import calculate_metrics_at_cutoff


class TestSensitivityMetrics:
    """Test cases for calculate_metrics_at_cutoff function."""

    def test_perfect_prediction(self):
        """Test when cutoff matches reference perfectly."""
        times = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        cutoff = 3.0
        reference = 3.0

        metrics = calculate_metrics_at_cutoff(times, cutoff, reference)

        assert metrics['tp'] == 2  # 1, 2 are <= 3
        assert metrics['tn'] == 2  # 4, 5 are > 3
        assert metrics['fp'] == 0
        assert metrics['fn'] == 0
        assert metrics['precision'] == 1.0
        assert metrics['recall'] == 1.0
        assert metrics['f1'] == 1.0

    def test_cutoff_too_low(self):
        """Test when cutoff is lower than reference, causing false negatives."""
        times = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        cutoff = 1.5  # Only 1 is predicted fast
        reference = 3.0  # 1, 2, 3 are actually fast

        metrics = calculate_metrics_at_cutoff(times, cutoff, reference)

        # TP: 1 (1.0 <= 1.5 and 1.0 <= 3.0)
        # FN: 2 (2.0, 3.0 are <= 3.0 but > 1.5)
        # FP: 0
        # TN: 2 (4.0, 5.0)
        assert metrics['tp'] == 1
        assert metrics['fn'] == 2
        assert metrics['fp'] == 0
        assert metrics['tn'] == 2

    def test_cutoff_too_high(self):
        """Test when cutoff is higher than reference, causing false positives."""
        times = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        cutoff = 4.5  # 1,2,3,4 predicted fast
        reference = 3.0  # 1,2,3 actually fast

        metrics = calculate_metrics_at_cutoff(times, cutoff, reference)

        # TP: 3 (1,2,3)
        # FN: 0
        # FP: 1 (4 is > 3 but <= 4.5)
        # TN: 1 (5)
        assert metrics['tp'] == 3
        assert metrics['fn'] == 0
        assert metrics['fp'] == 1
        assert metrics['tn'] == 1

    def test_zero_division_precision(self):
        """Test handling of zero division when no positives are predicted."""
        times = np.array([5.0, 6.0, 7.0])
        cutoff = 1.0  # No items predicted as fast
        reference = 5.0  # 5 is actually fast

        metrics = calculate_metrics_at_cutoff(times, cutoff, reference)

        assert metrics['precision'] == 0.0
        assert metrics['recall'] == 0.0
        assert metrics['f1'] == 0.0

    def test_zero_division_recall(self):
        """Test handling of zero division when no actual positives exist."""
        times = np.array([10.0, 20.0, 30.0])
        cutoff = 15.0
        reference = 5.0  # No items are actually fast

        metrics = calculate_metrics_at_cutoff(times, cutoff, reference)

        # All are TN or FP
        assert metrics['tp'] == 0
        assert metrics['fn'] == 0
        assert metrics['recall'] == 0.0

    def test_fpr_fnr_calculation(self):
        """Test calculation of False Positive and False Negative rates."""
        times = np.array([1.0, 2.0, 3.0, 4.0])
        cutoff = 2.5
        reference = 2.5

        # With perfect cutoff:
        # TP=2 (1,2), TN=2 (3,4), FP=0, FN=0
        # FPR = 0 / (0+2) = 0
        # FNR = 0 / (0+2) = 0
        metrics = calculate_metrics_at_cutoff(times, cutoff, reference)
        assert metrics['fpr'] == 0.0
        assert metrics['fnr'] == 0.0

        # Now shift cutoff to create FP and FN
        cutoff = 3.5
        # Predicted fast: 1,2,3. Actual fast: 1,2
        # TP=2, FN=0, FP=1 (3), TN=1 (4)
        # FPR = 1 / (1+1) = 0.5
        # FNR = 0 / (2+0) = 0.0
        metrics = calculate_metrics_at_cutoff(times, cutoff, reference)
        assert metrics['fpr'] == 0.5
        assert metrics['fnr'] == 0.0
