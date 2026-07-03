import pytest
import numpy as np
import sys
import os
from pathlib import Path
import logging

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from preprocessing.scaling import standardize_data, min_max_scale, robust_scale
from simulation.logger import setup_logger

# Initialize logger for tests
test_logger = setup_logger("test_scaling")

class TestStandardization:
    def test_standardize_mean_zero(self):
        """Contract test: Standardization should result in mean ~ 0"""
        data = np.random.rand(100, 5) * 100
        scaled = standardize_data(data)
        means = np.mean(scaled, axis=0)
        assert np.allclose(means, 0, atol=1e-7), f"Means should be close to 0, got {means}"

    def test_standardize_std_one(self):
        """Contract test: Standardization should result in std ~ 1"""
        data = np.random.rand(100, 5) * 100
        scaled = standardize_data(data)
        stds = np.std(scaled, axis=0)
        assert np.allclose(stds, 1, atol=1e-7), f"Stds should be close to 1, got {stds}"

class TestMinMaxScaling:
    def test_minmax_min_zero(self):
        """Contract test: Min-Max scaling should result in min ~ 0"""
        data = np.random.rand(100, 5) * 100
        scaled = min_max_scale(data)
        mins = np.min(scaled, axis=0)
        assert np.allclose(mins, 0, atol=1e-7), f"Mins should be close to 0, got {mins}"

    def test_minmax_max_one(self):
        """Contract test: Min-Max scaling should result in max ~ 1"""
        data = np.random.rand(100, 5) * 100
        scaled = min_max_scale(data)
        maxs = np.max(scaled, axis=0)
        assert np.allclose(maxs, 1, atol=1e-7), f"Maxs should be close to 1, got {maxs}"

class TestRobustScaling:
    def test_robust_median_zero(self):
        """Contract test: Robust scaling should result in median ~ 0"""
        # Generate data with a known median (e.g., 50)
        data = np.random.normal(loc=50, scale=10, size=(100, 5))
        scaled = robust_scale(data)
        medians = np.median(scaled, axis=0)
        assert np.allclose(medians, 0, atol=1e-2), f"Medians should be close to 0, got {medians}"

    def test_robust_iqr_unit(self):
        """Contract test: Robust scaling should result in IQR ~ 1 (or 0.6745 for normal)"""
        # For a standard normal distribution, IQR is approx 1.35 (0.6745 - -0.6745)
        # After scaling by IQR, the IQR of the scaled data should be 1.
        # We use a larger sample to ensure stability.
        data = np.random.normal(loc=0, scale=1, size=(1000, 5))
        scaled = robust_scale(data)
        
        # Calculate IQR for each column
        q75 = np.percentile(scaled, 75, axis=0)
        q25 = np.percentile(scaled, 25, axis=0)
        iqr = q75 - q25
        
        # The IQR of the scaled data should be 1.0
        assert np.allclose(iqr, 1.0, atol=1e-2), f"IQR should be close to 1.0, got {iqr}"

    def test_robust_zero_iqr_handling(self):
        """Contract test: Robust scaling should handle zero IQR gracefully (log warning)"""
        # Create data with zero variance (constant)
        data = np.ones((100, 5))
        
        # Capture log output
        with self.assertLogs('simulation.logger', level='WARNING') as cm:
            scaled = robust_scale(data)
            
            # Check that a warning was logged
            assert any("zero IQR" in msg.lower() or "skipping" in msg.lower() for msg in cm.output), \
                "Expected a warning log about zero IQR"
        
        # The output should be zeros (or handled gracefully without crashing)
        # Depending on implementation, it might be all zeros or the original data.
        # Based on the task description "skip iteration", we expect a safe fallback.
        # If the implementation returns zeros for constant columns:
        assert np.all(scaled == 0) or np.allclose(scaled, 0), \
            "Output should be zeros for constant input if IQR is zero"

    def test_robust_2d_array(self):
        """Test robust scaling works on 2D arrays"""
        data = np.random.normal(loc=10, scale=5, size=(200, 3))
        scaled = robust_scale(data)
        assert scaled.shape == data.shape, "Shape should be preserved"

    def test_robust_1d_array(self):
        """Test robust scaling works on 1D arrays"""
        data = np.random.normal(loc=10, scale=5, size=200)
        scaled = robust_scale(data)
        assert scaled.shape == data.shape, "Shape should be preserved"
        
    def test_robust_with_outliers(self):
        """Test that robust scaling is less sensitive to outliers than standardization"""
        # Create data with outliers
        base_data = np.random.normal(loc=0, scale=1, size=(100, 1))
        outliers = np.array([[100], [100], [100]])
        data_with_outliers = np.vstack([base_data, outliers])
        
        # Standardize
        std_scaled = standardize_data(data_with_outliers)
        # Robust scale
        rob_scaled = robust_scale(data_with_outliers)
        
        # The standard deviation of the standardized data will be 1, but the values for outliers will be large
        # The robust scale should keep the bulk of the data within a reasonable range
        # Check that the median of the robust scaled data is close to 0
        assert np.abs(np.median(rob_scaled)) < 0.1, "Median of robust scaled data should be close to 0"
        
        # Check that the IQR of the robust scaled data is close to 1
        q75 = np.percentile(rob_scaled, 75)
        q25 = np.percentile(rob_scaled, 25)
        iqr = q75 - q25
        assert np.abs(iqr - 1.0) < 0.1, f"IQR of robust scaled data should be close to 1.0, got {iqr}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])