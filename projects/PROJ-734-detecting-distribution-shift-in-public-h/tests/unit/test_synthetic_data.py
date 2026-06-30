"""
Unit tests for the synthetic data generator (T008).

These tests verify that the synthetic data generator correctly produces
data with the required pathological characteristics:
(a) Missing weeks (NaNs)
(b) Constant segments (zero variance)
(c) Outliers
"""
import pytest
import numpy as np
import pandas as pd
import os
import tempfile

# Import the module under test
from code.synthetic_data import generate_synthetic_ili_series, save_synthetic_data


class TestSyntheticDataGeneration:
    """Tests for the core generation logic."""

    def test_missing_weeks_generated(self):
        """Verify that missing weeks (NaNs) are generated."""
        df = generate_synthetic_ili_series(n_weeks=100, missing_rate=0.1, seed=42)
        missing_count = df['ili_percent'].isna().sum()
        expected_min = 5  # Expecting roughly 10% of 100
        assert missing_count > 0, "Expected at least some missing weeks."
        # Allow some variance due to randomness, but ensure it's in the ballpark
        assert missing_count >= 5, f"Expected ~10 missing weeks, got {missing_count}"

    def test_constant_segments_generated(self):
        """Verify that constant segments (zero variance) are generated."""
        df = generate_synthetic_ili_series(n_weeks=100, constant_segment_len=10, seed=42)
        constant_count = df['is_constant'].sum()
        assert constant_count >= 10, f"Expected at least 10 constant weeks, got {constant_count}"

        # Verify the values in the constant segment are actually constant
        constant_mask = df['is_constant']
        if constant_mask.any():
            constant_values = df.loc[constant_mask, 'ili_percent']
            # Check variance is zero (or very close due to float representation)
            assert constant_values.var() == 0.0, "Values in constant segment should have zero variance."

    def test_outliers_generated(self):
        """Verify that outliers are generated."""
        df = generate_synthetic_ili_series(n_weeks=100, outlier_rate=0.05, seed=42)
        outlier_count = df['is_outlier'].sum()
        expected_min = 2
        assert outlier_count >= expected_min, f"Expected at least {expected_min} outliers, got {outlier_count}"

        # Verify outliers are significantly different from the median
        median_val = df['ili_percent'].median()
        outlier_values = df.loc[df['is_outlier'], 'ili_percent']
        # Outliers should be either very high or very low
        for val in outlier_values:
            if not np.isnan(val):
                ratio = val / median_val
                assert ratio > 2.0 or ratio < 0.5, f"Value {val} is not an extreme outlier compared to median {median_val}"

    def test_reproducibility(self):
        """Verify that the same seed produces the same data."""
        df1 = generate_synthetic_ili_series(n_weeks=50, seed=123)
        df2 = generate_synthetic_ili_series(n_weeks=50, seed=123)
        assert df1.equals(df2), "Data should be identical for the same seed."

    def test_no_nan_in_constant_segment(self):
        """Verify that constant segments do not accidentally contain NaNs."""
        df = generate_synthetic_ili_series(n_weeks=100, missing_rate=0.1, constant_segment_len=10, seed=42)
        constant_mask = df['is_constant']
        if constant_mask.any():
            has_nan_in_constant = df.loc[constant_mask, 'ili_percent'].isna().any()
            assert not has_nan_in_constant, "Constant segments should not contain NaNs."


class TestSaveSyntheticData:
    """Tests for the file saving logic."""

    def test_save_creates_file(self):
        """Verify that save_synthetic_data creates a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_output.csv")
            result_path = save_synthetic_data(output_path=output_path, n_weeks=50, seed=42)
            
            assert os.path.exists(result_path), "Output file should exist."
            assert result_path == output_path, "Returned path should match input path."

    def test_save_creates_directory(self):
        """Verify that save_synthetic_data creates the directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nested_path = os.path.join(tmpdir, "subdir", "nested", "test.csv")
            result_path = save_synthetic_data(output_path=nested_path, n_weeks=50, seed=42)
            
            assert os.path.exists(result_path), "Output file should exist in nested directory."

    def test_save_data_integrity(self):
        """Verify that saved data matches in-memory data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test_integrity.csv")
            save_synthetic_data(output_path=output_path, n_weeks=50, seed=42)
            
            df_saved = pd.read_csv(output_path)
            df_in_memory = generate_synthetic_ili_series(n_weeks=50, seed=42)
            
            # Compare shapes
            assert df_saved.shape == df_in_memory.shape, "Shapes should match."
            
            # Compare values (allowing for float comparison issues)
            pd.testing.assert_frame_equal(df_saved, df_in_memory)