import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from ingestion.preprocess import scrub_and_regression, calculate_fd_series, FD_THRESHOLD

class TestScrubbingAndRegression:
    @pytest.fixture
    def sample_timeseries(self):
        # Create a small synthetic time series for testing the logic
        # 100 time points, 5 ROIs
        np.random.seed(42)
        data = np.random.randn(100, 5)
        return pd.DataFrame(data, columns=[f"ROI_{i}" for i in range(5)])

    @pytest.fixture
    def sample_motion(self):
        # Create motion parameters
        # Inject some high motion at specific time points
        np.random.seed(123)
        motion = pd.DataFrame(
            np.random.randn(100, 6) * 0.05,
            columns=['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
        )
        # Inject a spike in motion at index 50 to trigger scrubbing
        motion.loc[50, 'trans_x'] = 1.0  # Large motion
        return motion

    def test_fd_calculation(self, sample_motion):
        fd = calculate_fd_series(sample_motion)
        assert len(fd) == 100
        assert fd.iloc[50] > FD_THRESHOLD, "Injected motion should exceed threshold"

    def test_scrubbing_reduces_length(self, sample_timeseries, sample_motion):
        fd = calculate_fd_series(sample_motion)
        cleaned = scrub_and_regression(sample_timeseries, sample_motion, fd)
        
        # We injected a spike at index 50 which should be scrubbed
        # The length should be less than 100
        assert len(cleaned) < len(sample_timeseries), "Scrubbing should remove time points"
        assert 50 not in cleaned.index, "Time point 50 should be removed"

    def test_regression_residuals(self, sample_timeseries, sample_motion):
        fd = calculate_fd_series(sample_motion)
        cleaned = scrub_and_regression(sample_timeseries, sample_motion, fd)
        
        # The cleaned data should have similar statistical properties
        # (mean close to 0) but not identical to original
        assert cleaned.mean().abs().mean() < 1.0, "Residuals should be centered"
        
    def test_output_shape_consistency(self, sample_timeseries, sample_motion):
        fd = calculate_fd_series(sample_motion)
        cleaned = scrub_and_regression(sample_timeseries, sample_motion, fd)
        
        # Columns should remain the same
        assert list(cleaned.columns) == list(sample_timeseries.columns)
        # Index should be a subset
        assert set(cleaned.index).issubset(set(sample_timeseries.index))
