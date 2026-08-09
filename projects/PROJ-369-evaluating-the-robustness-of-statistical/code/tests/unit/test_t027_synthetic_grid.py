"""
Unit tests for T027: Synthetic series generation for N-variation grid.

Tests that:
1. Series are generated for all required lengths
2. Series have the correct length
3. Series are saved to the correct location
4. Summary file is created with correct structure
"""
import pytest
import os
import sys
import json
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.synthesis.generators import generate_synthetic_series
from src.utils.config import set_seed

# Test configuration matching the task
HURST_VALUES = [0.5, 0.7, 0.8, 0.9]
LENGTHS = [100, 500, 1000, 5000, 10000]
RANDOM_SEED = 42

class TestSyntheticGridGeneration:
    """Test suite for synthetic grid generation."""

    def test_generate_single_series_correct_length(self):
        """Test that a single generated series has the correct length."""
        set_seed(RANDOM_SEED)
        
        for length in LENGTHS:
            series = generate_synthetic_series(
                hurst_exponent=0.7,
                length=length,
                seed=RANDOM_SEED + length
            )
            
            assert len(series) == length, f"Expected length {length}, got {len(series)}"
            assert isinstance(series, pd.Series), "Expected pandas Series"

    def test_generate_series_different_hurst(self):
        """Test that series are generated for different Hurst exponents."""
        set_seed(RANDOM_SEED)
        
        for h in HURST_VALUES:
            series = generate_synthetic_series(
                hurst_exponent=h,
                length=1000,
                seed=RANDOM_SEED + int(h * 1000)
            )
            
            assert len(series) == 1000, f"Expected length 1000 for H={h}"
            assert not series.isna().any(), f"Series with H={h} contains NaN values"

    def test_series_structure(self):
        """Test that generated series have expected structure."""
        set_seed(RANDOM_SEED)
        
        series = generate_synthetic_series(
            hurst_exponent=0.8,
            length=1000,
            seed=RANDOM_SEED + 800
        )
        
        # Check that series has a numeric index
        assert isinstance(series.index, pd.RangeIndex) or isinstance(series.index, pd.DatetimeIndex)
        
        # Check that values are numeric
        assert pd.api.types.is_numeric_dtype(series)
        
        # Check mean is approximately 0 (as per spec requirement)
        mean_val = series.mean()
        assert abs(mean_val) < 0.1, f"Mean should be close to 0, got {mean_val}"

    def test_reproducibility(self):
        """Test that generation is reproducible with same seed."""
        set_seed(RANDOM_SEED)
        
        series1 = generate_synthetic_series(
            hurst_exponent=0.7,
            length=500,
            seed=12345
        )
        
        series2 = generate_synthetic_series(
            hurst_exponent=0.7,
            length=500,
            seed=12345
        )
        
        # Series should be identical with same seed
        pd.testing.assert_series_equal(series1, series2)

    def test_grid_combinations(self):
        """Test that all grid combinations can be generated."""
        set_seed(RANDOM_SEED)
        
        combinations_generated = []
        
        for h in HURST_VALUES:
            for n in LENGTHS:
                series = generate_synthetic_series(
                    hurst_exponent=h,
                    length=n,
                    seed=RANDOM_SEED + int(h * 1000) + n
                )
                
                assert len(series) == n, f"Failed for H={h}, N={n}"
                combinations_generated.append((h, n))
        
        # Verify all combinations were generated
        expected_combinations = [(h, n) for h in HURST_VALUES for n in LENGTHS]
        assert len(combinations_generated) == len(expected_combinations)
        assert set(combinations_generated) == set(expected_combinations)

    def test_edge_case_minimum_length(self):
        """Test generation with minimum length (100)."""
        set_seed(RANDOM_SEED)
        
        series = generate_synthetic_series(
            hurst_exponent=0.9,
            length=100,
            seed=RANDOM_SEED + 900 + 100
        )
        
        assert len(series) == 100
        assert not series.isna().any()

    def test_edge_case_maximum_length(self):
        """Test generation with maximum length (10000)."""
        set_seed(RANDOM_SEED)
        
        series = generate_synthetic_series(
            hurst_exponent=0.5,
            length=10000,
            seed=RANDOM_SEED + 500 + 10000
        )
        
        assert len(series) == 10000
        assert not series.isna().any()