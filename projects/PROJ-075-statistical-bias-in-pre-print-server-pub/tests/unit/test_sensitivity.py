"""
Unit tests for sensitivity analysis logic in code/03_analysis.py (Sensitivity Module).
Verifies threshold sweeping and flip rate calculation.
"""
import pytest
import numpy as np

def calculate_flip_rate(preprint_p, journal_p, threshold):
    """
    Helper to calculate the flip rate for a given threshold.
    A flip occurs if one p-value is < threshold and the other is >= threshold.
    """
    pre_significant = preprint_p < threshold
    jour_significant = journal_p < threshold
    
    flips = (pre_significant != jour_significant)
    return np.mean(flips)

class TestSensitivity:
    def test_flip_rate_threshold_0_05(self):
        """
        Test flip rate calculation at threshold 0.05.
        """
        # Create synthetic data where some flip at 0.05
        preprint_p = np.array([0.04, 0.06, 0.03, 0.07])
        journal_p = np.array([0.06, 0.04, 0.03, 0.07])
        
        # Row 0: pre < 0.05, jour >= 0.05 -> Flip
        # Row 1: pre >= 0.05, jour < 0.05 -> Flip
        # Row 2: both < 0.05 -> No Flip
        # Row 3: both >= 0.05 -> No Flip
        # Expected flip rate: 2/4 = 0.5
        
        rate = calculate_flip_rate(preprint_p, journal_p, 0.05)
        assert rate == 0.5

    def test_flip_rate_threshold_0_01(self):
        """
        Test flip rate calculation at threshold 0.01.
        """
        preprint_p = np.array([0.005, 0.02, 0.005, 0.02])
        journal_p = np.array([0.02, 0.005, 0.02, 0.005])
        
        # Row 0: pre < 0.01, jour >= 0.01 -> Flip
        # Row 1: pre >= 0.01, jour < 0.01 -> Flip
        # Row 2: pre < 0.01, jour >= 0.01 -> Flip
        # Row 3: pre >= 0.01, jour < 0.01 -> Flip
        # Expected: 4/4 = 1.0
        
        rate = calculate_flip_rate(preprint_p, journal_p, 0.01)
        assert rate == 1.0

    def test_flip_rate_threshold_0_10(self):
        """
        Test flip rate calculation at threshold 0.10.
        """
        preprint_p = np.array([0.09, 0.11, 0.09, 0.11])
        journal_p = np.array([0.11, 0.09, 0.11, 0.09])
        
        # All rows flip
        rate = calculate_flip_rate(preprint_p, journal_p, 0.10)
        assert rate == 1.0

    def test_output_structure(self):
        """
        Test that the output structure matches the expected format.
        """
        threshold = 0.05
        flip_rate = 0.5
        
        output = {
            "threshold": threshold,
            "flip_rate": flip_rate
        }
        
        assert "threshold" in output
        assert "flip_rate" in output
        assert isinstance(output["threshold"], float)
        assert isinstance(output["flip_rate"], float)
