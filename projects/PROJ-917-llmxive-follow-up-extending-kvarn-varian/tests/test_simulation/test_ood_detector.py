"""
Unit tests for OOD Detection mechanism (T035a).
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path

# Import the module under test
from code.simulation.ood_detector import OODDetector, OODResult, detect_ood


class TestOODDetector:

    def setup_method(self):
        """Setup test fixtures."""
        self.moments_valid = {
            'mean': 0.5,
            'variance': 0.1,
            'sparsity': 0.2,
            'outlier_magnitude': 2.0
        }
        self.moments_nan = {
            'mean': np.nan,
            'variance': 0.1,
            'sparsity': 0.2,
            'outlier_magnitude': 2.0
        }
        self.moments_low_var = {
            'mean': 0.5,
            'variance': 1e-9, # Below default epsilon floor
            'sparsity': 0.2,
            'outlier_magnitude': 2.0
        }
        self.moments_high_outlier = {
            'mean': 0.5,
            'variance': 0.1,
            'sparsity': 0.2,
            'outlier_magnitude': 20.0 # Above default threshold
        }

    def test_numerical_stability_pass(self):
        """Test that valid moments pass numerical stability check."""
        detector = OODDetector()
        result = detector.check_numerical_stability(self.moments_valid)
        assert result[0] is True
        assert "passed" in result[1]

    def test_numerical_stability_nan(self):
        """Test that NaN values trigger instability."""
        detector = OODDetector()
        result = detector.check_numerical_stability(self.moments_nan)
        assert result[0] is False
        assert "Non-finite" in result[1]

    def test_epsilon_floor_check(self):
        """Test that variance below epsilon floor is flagged."""
        detector = OODDetector(epsilon_floor=1e-6)
        result = detector.check_numerical_stability(self.moments_low_var)
        assert result[0] is False
        assert "epsilon_floor" in result[1]

    def test_outlier_threshold_pass(self):
        """Test that valid outlier magnitude passes."""
        detector = OODDetector(outlier_threshold=10.0)
        result = detector.check_outlier_threshold(self.moments_valid)
        assert result[0] is True

    def test_outlier_threshold_fail(self):
        """Test that high outlier magnitude is flagged."""
        detector = OODDetector(outlier_threshold=5.0)
        result = detector.check_outlier_threshold(self.moments_high_outlier)
        assert result[0] is False
        assert "exceeds threshold" in result[1]

    def test_statistical_ood_no_reference(self):
        """Test that statistical check passes if no reference data is provided."""
        detector = OODDetector()
        result = detector.check_statistical_distance(self.moments_valid)
        assert result[0] is False
        assert "No reference" in result[1]

    def test_statistical_ood_detection(self):
        """Test statistical OOD detection with reference data."""
        # Create a temporary CSV with training stats
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Create a dataset where mean=0.5, std=0.01
            # So a value of 0.6 is 10 std devs away
            df = pd.DataFrame({
                'mean': [0.5] * 100,
                'variance': [0.1] * 100,
                'sparsity': [0.2] * 100,
                'outlier_magnitude': [2.0] * 100
            })
            # Introduce slight variance to std calculation
            df.loc[0, 'mean'] = 0.51
            df.to_csv(f.name, index=False)
            temp_path = Path(f.name)

        try:
            detector = OODDetector(training_moments_path=temp_path, std_factor=3.0)
            # Input with mean=0.6 (should be OOD)
            bad_moments = {
                'mean': 0.6,
                'variance': 0.1,
                'sparsity': 0.2,
                'outlier_magnitude': 2.0
            }
            result = detector.check_statistical_distance(bad_moments)
            assert result[0] is True
            assert "z-score" in result[1]
        finally:
            os.unlink(temp_path)

    def test_full_detect_ood(self):
        """Test full detect method returns OODResult correctly."""
        detector = OODDetector(outlier_threshold=5.0)
        result = detector.detect(self.moments_high_outlier)
        assert isinstance(result, OODResult)
        assert result.is_ood is True
        assert "Outlier" in result.reason

    def test_full_detect_valid(self):
        """Test full detect method returns valid result."""
        detector = OODDetector(outlier_threshold=10.0)
        result = detector.detect(self.moments_valid)
        assert result.is_ood is False
        assert "passed" in result.reason

    def test_convenience_function(self):
        """Test the top-level detect_ood function."""
        result = detect_ood(self.moments_valid, outlier_threshold=10.0)
        assert result.is_ood is False

        result = detect_ood(self.moments_low_var, epsilon_floor=1e-6)
        assert result.is_ood is True
