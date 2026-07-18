import pytest
import math
import os
import sys
import tempfile
from pathlib import Path
import csv

# Import the functions we are testing
# Adjust import path based on project structure
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from src.analysis.distribution_test import (
    extract_maximal_gaps_in_windows,
    normalize_maximal_gaps,
    gue_extreme_value_cdf,
    compute_empirical_cdf,
    run_ks_test,
    load_primes_gaps
)

class TestExtractMaximalGapsInWindows:
    def test_empty_data(self):
        assert extract_maximal_gaps_in_windows([]) == []

    def test_single_window(self):
        # Create mock data: 5 gaps in one window
        # Format: (p_before, p_after, gap, norm_gap)
        data = [
            (2, 3, 1, 0.1),
            (3, 5, 2, 0.2),
            (5, 7, 2, 0.15),
            (7, 11, 4, 0.3),
            (11, 13, 2, 0.1)
        ]
        result = extract_maximal_gaps_in_windows(data, window_size=5)
        assert len(result) == 1
        assert result[0] == 0.3  # Max is 0.3

    def test_multiple_windows(self):
        # 10 gaps, window size 5 -> 2 windows
        data = [
            (1, 2, 1, 0.1), (2, 3, 1, 0.2), (3, 4, 1, 0.3), (4, 5, 1, 0.4), (5, 6, 1, 0.5), # Max 0.5
            (6, 7, 1, 0.1), (7, 8, 1, 0.2), (8, 9, 1, 0.1), (9, 10, 1, 0.3), (10, 11, 1, 0.4) # Max 0.4
        ]
        result = extract_maximal_gaps_in_windows(data, window_size=5)
        assert len(result) == 2
        assert result[0] == 0.5
        assert result[1] == 0.4

class TestNormalizeMaximalGaps:
    def test_identity(self):
        # Since input is expected to be already normalized, this should be identity
        data = [0.1, 0.5, 0.9]
        assert normalize_maximal_gaps(data) == data

class TestGUEExtremeValueCDF:
    def test_small_x(self):
        # For very small x, CDF should be close to 0
        assert gue_extreme_value_cdf(-10) < 1e-4

    def test_zero(self):
        # exp(-exp(0)) = exp(-1) ≈ 0.3678
        expected = math.exp(-1)
        assert abs(gue_extreme_value_cdf(0) - expected) < 1e-6

    def test_large_x(self):
        # For large x, CDF should be close to 1
        assert gue_extreme_value_cdf(10) > 0.99

class TestComputeEmpiricalCDF:
    def test_simple_data(self):
        data = [1, 2, 3]
        x, cdf = compute_empirical_cdf(data)
        assert x == [1, 2, 3]
        assert cdf == [1/3, 2/3, 3/3]

    def test_unsorted_data(self):
        data = [3, 1, 2]
        x, cdf = compute_empirical_cdf(data)
        assert x == [1, 2, 3]
        assert cdf == [1/3, 2/3, 1.0]

class TestRunKSTest:
    def test_perfect_match(self):
        # If empirical and theoretical are identical, D should be 0
        x = [0.0, 0.5, 1.0]
        cdf = [gue_extreme_value_cdf(val) for val in x]
        D, p = run_ks_test(x, cdf, gue_extreme_value_cdf)
        assert D == 0.0
        assert p == 1.0

    def test_empty_data(self):
        D, p = run_ks_test([], [], gue_extreme_value_cdf)
        assert D == 0.0
        assert p == 1.0

class TestLoadPrimesGaps:
    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_primes_gaps("non_existent_file.csv")

    def test_load_valid_csv(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            f.write("prime_before,prime_after,gap_size,normalized_gap\n")
            f.write("2,3,1,0.1\n")
            f.write("3,5,2,0.2\n")
            temp_path = f.name

        try:
            data = load_primes_gaps(temp_path)
            assert len(data) == 2
            assert data[0] == (2, 3, 1, 0.1)
            assert data[1] == (3, 5, 2, 0.2)
        finally:
            os.unlink(temp_path)
