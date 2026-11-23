"""
Unit tests for T057: Time-Bound Baseline Validation.
"""
import pytest
import os
import tempfile
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.analysis.validate_metrics import (
    validate_time_bound_baseline,
    validate_metrics_directory,
    scan_parquet_for_nans
)

class TestT057Validation:
    """Tests for time-bound baseline validation logic."""

    def test_validate_time_bound_flag_present(self):
        """Test validation when Time-Bound flag is present and steps >= 1000."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "baseline_partial.parquet")
            
            # Create a DataFrame with Time-Bound status and 1500 steps
            df = pd.DataFrame({
                'step': range(1500),
                'status': ['Time-Bound'] * 1500,
                'value': np.random.rand(1500)
            })
            df.to_parquet(file_path)
            
            has_flag, meets_steps, msg = validate_time_bound_baseline(file_path, min_steps=1000)
            
            assert has_flag is True
            assert meets_steps is True
            assert "passed" in msg.lower()

    def test_validate_time_bound_flag_missing(self):
        """Test validation when Time-Bound flag is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "baseline_partial.parquet")
            
            # Create a DataFrame without Time-Bound status
            df = pd.DataFrame({
                'step': range(1500),
                'status': ['Running'] * 1500,
                'value': np.random.rand(1500)
            })
            df.to_parquet(file_path)
            
            has_flag, meets_steps, msg = validate_time_bound_baseline(file_path, min_steps=1000)
            
            assert has_flag is False
            assert "Missing" in msg

    def test_validate_insufficient_steps(self):
        """Test validation when steps < 1000."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "baseline_partial.parquet")
            
            # Create a DataFrame with Time-Bound status but only 500 steps
            df = pd.DataFrame({
                'step': range(500),
                'status': ['Time-Bound'] * 500,
                'value': np.random.rand(500)
            })
            df.to_parquet(file_path)
            
            has_flag, meets_steps, msg = validate_time_bound_baseline(file_path, min_steps=1000)
            
            assert has_flag is True
            assert meets_steps is False
            assert "steps" in msg.lower()

    def test_validate_file_not_found(self):
        """Test validation when file does not exist."""
        has_flag, meets_steps, msg = validate_time_bound_baseline(
            "/nonexistent/path/baseline_partial.parquet", 
            min_steps=1000
        )
        
        assert has_flag is False
        assert meets_steps is False
        assert "not found" in msg.lower()

    def test_validate_metrics_directory_success(self):
        """Test directory validation when all checks pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid baseline_partial.parquet
            baseline_path = os.path.join(tmpdir, "baseline_partial.parquet")
            df = pd.DataFrame({
                'step': range(1500),
                'status': ['Time-Bound'] * 1500,
                'value': np.random.rand(1500)
            })
            df.to_parquet(baseline_path)
            
            # Create another valid parquet file
            other_path = os.path.join(tmpdir, "other_run.parquet")
            df2 = pd.DataFrame({
                'step': range(100),
                'value': np.random.rand(100)
            })
            df2.to_parquet(other_path)
            
            success = validate_metrics_directory(tmpdir, min_steps=1000)
            
            assert success is True

    def test_validate_metrics_directory_missing_baseline(self):
        """Test directory validation when baseline is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create only other parquet files, no baseline
            other_path = os.path.join(tmpdir, "other_run.parquet")
            df = pd.DataFrame({
                'step': range(100),
                'value': np.random.rand(100)
            })
            df.to_parquet(other_path)
            
            success = validate_metrics_directory(tmpdir, min_steps=1000)
            
            assert success is False

    def test_validate_metrics_directory_nan_in_file(self):
        """Test directory validation when a file contains NaN values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create valid baseline
            baseline_path = os.path.join(tmpdir, "baseline_partial.parquet")
            df = pd.DataFrame({
                'step': range(1500),
                'status': ['Time-Bound'] * 1500,
                'value': np.random.rand(1500)
            })
            df.to_parquet(baseline_path)
            
            # Create file with NaN
            nan_path = os.path.join(tmpdir, "bad_run.parquet")
            df_nan = pd.DataFrame({
                'step': range(100),
                'value': [np.nan if i % 10 == 0 else i for i in range(100)]
            })
            df_nan.to_parquet(nan_path)
            
            success = validate_metrics_directory(tmpdir, min_steps=1000)
            
            assert success is False

    def test_scan_parquet_for_nans_clean(self):
        """Test NaN scan on a clean file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "clean.parquet")
            df = pd.DataFrame({
                'a': [1, 2, 3],
                'b': [4.0, 5.0, 6.0]
            })
            df.to_parquet(file_path)
            
            has_nans, count = scan_parquet_for_nans(file_path)
            
            assert has_nans is False
            assert count == 0

    def test_scan_parquet_for_nans_with_nans(self):
        """Test NaN scan on a file with NaN values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "dirty.parquet")
            df = pd.DataFrame({
                'a': [1, np.nan, 3],
                'b': [4.0, 5.0, np.nan]
            })
            df.to_parquet(file_path)
            
            has_nans, count = scan_parquet_for_nans(file_path)
            
            assert has_nans is True
            assert count == 2
