"""
Unit tests for the filtering logic in code/src/filter.py.

These tests verify:
1. Threshold grid generation dimensions and values.
2. Handling of missing values (NA/NaN) in input data.
3. Correct counting of detections based on thresholds.
"""
import pytest
import pandas as pd
import numpy as np
from src.filter import generate_threshold_grid, filter_by_thresholds

class TestThresholdGridGeneration:
    def test_grid_dimensions(self):
        """Verify that the grid covers SNR 5-20 and Morph 0.3-0.9 with correct steps."""
        snr_range = range(5, 21, 1)
        morph_range = np.arange(0.3, 0.95, 0.1)
        
        grid = generate_threshold_grid(snr_range, morph_range)
        
        # Check SNR count: 5, 6, ..., 20 -> 16 values
        assert len(grid) == 16 * len(morph_range)
        
        # Verify specific values exist
        snr_values = sorted(list(set(row['snr_threshold'] for row in grid)))
        assert snr_values[0] == 5
        assert snr_values[-1] == 20
        assert len(snr_values) == 16

    def test_grid_includes_upper_bound(self):
        """Explicitly ensure the grid includes a representative threshold value near the upper bound."""
        grid = generate_threshold_grid(range(5, 21, 1), np.arange(0.3, 0.95, 0.1))
        snr_values = sorted(list(set(row['snr_threshold'] for row in grid)))
        # 20 is the upper bound of the range(5, 21, 1)
        assert 20 in snr_values
        # 0.9 is the last value in arange(0.3, 0.95, 0.1)
        morph_values = sorted(list(set(row['morph_threshold'] for row in grid)))
        assert 0.9 in morph_values

class TestMissingValueHandling:
    def test_exclusion_of_nan_snr(self):
        """Verify that rows with NaN SNR are excluded without crashing."""
        df = pd.DataFrame({
            'snr': [10.0, np.nan, 15.0, 5.0],
            'morph': [0.5, 0.5, 0.5, 0.5],
            'ra': [1, 2, 3, 4],
            'dec': [1, 2, 3, 4],
            'is_lens': [True, True, False, True]
        })
        
        # Should not raise an error
        result = filter_by_thresholds(df, snr_threshold=8.0, morph_threshold=0.4)
        
        # The row with NaN SNR should be excluded
        # Expected: 10.0 and 15.0 pass, 5.0 fails
        assert len(result) == 2
        assert 2 not in result.index  # Index 2 had NaN

    def test_exclusion_of_nan_morph(self):
        """Verify that rows with NaN Morphology are excluded without crashing."""
        df = pd.DataFrame({
            'snr': [10.0, 15.0, 5.0, 12.0],
            'morph': [0.5, np.nan, 0.5, 0.5],
            'ra': [1, 2, 3, 4],
            'dec': [1, 2, 3, 4],
            'is_lens': [True, True, False, True]
        })
        
        result = filter_by_thresholds(df, snr_threshold=8.0, morph_threshold=0.4)
        
        # Row with NaN morph (index 1) should be excluded
        # Row with snr=5.0 (index 2) should be excluded
        assert len(result) == 2
        assert 1 not in result.index

    def test_exclusion_of_string_na(self):
        """Verify that rows with string 'NA' or 'N/A' are excluded."""
        df = pd.DataFrame({
            'snr': [10.0, 'NA', 15.0, 'N/A'],
            'morph': [0.5, 0.5, 0.5, 0.5],
            'ra': [1, 2, 3, 4],
            'dec': [1, 2, 3, 4],
            'is_lens': [True, True, False, True]
        })
        
        # Convert to numeric, coercing errors to NaN
        df['snr'] = pd.to_numeric(df['snr'], errors='coerce')
        
        result = filter_by_thresholds(df, snr_threshold=8.0, morph_threshold=0.4)
        
        # Rows with 'NA' and 'N/A' converted to NaN should be excluded
        assert len(result) == 2

class TestFilterLogic:
    def test_basic_filtering(self):
        """Test basic filtering logic with valid data."""
        df = pd.DataFrame({
            'snr': [5.0, 10.0, 15.0, 20.0],
            'morph': [0.2, 0.5, 0.8, 0.9],
            'ra': [1, 2, 3, 4],
            'dec': [1, 2, 3, 4],
            'is_lens': [True, True, False, True]
        })
        
        # Filter: SNR >= 10, Morph >= 0.4
        result = filter_by_thresholds(df, snr_threshold=10.0, morph_threshold=0.4)
        
        # Expected: 10.0 (pass), 15.0 (pass), 20.0 (pass). 5.0 (fail SNR), 0.2 (fail Morph)
        # Wait, row 0: snr=5 (fail), row 1: snr=10 (pass), row 2: snr=15 (pass), row 3: snr=20 (pass)
        # Row 0: morph=0.2 (fail). Row 1: morph=0.5 (pass). Row 2: morph=0.8 (pass). Row 3: morph=0.9 (pass).
        # So rows 1, 2, 3 should pass.
        assert len(result) == 3
        assert list(result.index) == [1, 2, 3]

    def test_empty_result(self):
        """Test filtering when no rows meet the criteria."""
        df = pd.DataFrame({
            'snr': [2.0, 3.0],
            'morph': [0.1, 0.2],
            'ra': [1, 2],
            'dec': [1, 2],
            'is_lens': [True, False]
        })
        
        result = filter_by_thresholds(df, snr_threshold=10.0, morph_threshold=0.4)
        
        assert len(result) == 0
        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == list(df.columns)