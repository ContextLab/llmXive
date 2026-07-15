import pytest
import math
import os
import sys
import tempfile
from pathlib import Path
import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.distribution_test import (
    load_primes_gaps,
    extract_maximal_gaps_in_windows,
    normalize_maximal_gaps,
    gue_extreme_value_cdf,
    compute_empirical_cdf,
    run_ks_test,
    plot_cdf_comparison
)

class TestNormalizeMaximalGaps:
    def test_normalize_pass_through(self):
        """Test that normalization currently passes through as per implementation."""
        data = [1.0, 2.0, 3.0]
        result = normalize_maximal_gaps(data)
        assert result == data

class TestGUEExtremeValueCDF:
    def test_cdf_monotonicity(self):
        """CDF should be non-decreasing."""
        x_vals = np.linspace(-2, 4, 100)
        cdf_vals = [gue_extreme_value_cdf(x) for x in x_vals]
        for i in range(1, len(cdf_vals)):
            assert cdf_vals[i] >= cdf_vals[i-1] - 1e-9

    def test_cdf_range(self):
        """CDF values should be in [0, 1]."""
        x_vals = np.linspace(-5, 10, 50)
        for x in x_vals:
            val = gue_extreme_value_cdf(x)
            assert 0.0 <= val <= 1.0

class TestComputeEmpiricalCDF:
    def test_simple_cdf(self):
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        sorted_x, cdf_y = compute_empirical_cdf(data)
        assert list(sorted_x) == [1.0, 2.0, 3.0, 4.0, 5.0]
        assert list(cdf_y) == [0.2, 0.4, 0.6, 0.8, 1.0]

    def test_empty_data(self):
        sorted_x, cdf_y = compute_empirical_cdf([])
        assert len(sorted_x) == 0
        assert len(cdf_y) == 0

class TestRunKSTest:
    def test_ks_test_with_known_distribution(self):
        """Test KS test with a known theoretical distribution (Normal)."""
        # Generate data from a standard normal (approx)
        np.random.seed(42)
        data = np.random.normal(0, 1, 1000)
        
        # Use scipy's norm.cdf as theoretical
        from scipy import stats
        result = run_ks_test(data, stats.norm.cdf)
        
        assert "statistic" in result
        assert "pvalue" in result
        assert 0 <= result["statistic"] <= 1
        assert 0 <= result["pvalue"] <= 1

    def test_ks_test_empty_data(self):
        result = run_ks_test([], gue_extreme_value_cdf)
        assert "error" in result

class TestExtractMaximalGapsInWindows:
    def test_window_extraction(self):
        # Create synthetic data: 10 items, window size 3
        # Data format: (prime_before, prime_after, gap_size, norm_gap)
        synthetic_data = [
            (10, 12, 2, 0.1),
            (12, 14, 2, 0.2),
            (14, 18, 4, 0.3), # Window 1 max: 0.3
            (18, 20, 2, 0.1),
            (20, 22, 2, 0.4), # Window 2 max: 0.4
            (22, 24, 2, 0.2),
            (24, 26, 2, 0.5), # Window 3 max: 0.5
            (26, 28, 2, 0.1),
            (28, 30, 2, 0.2),
            (30, 32, 2, 0.3)
        ]
        
        result = extract_maximal_gaps_in_windows(synthetic_data, window_size=3)
        
        assert len(result) == 3
        assert result[0] == 0.3
        assert result[1] == 0.4
        assert result[2] == 0.5

    def test_uneven_window(self):
        synthetic_data = [
            (10, 12, 2, 0.1),
            (12, 14, 2, 0.5),
            (14, 18, 4, 0.2)
        ]
        # Window size 5 -> should return 1 window (remainder handled)
        result = extract_maximal_gaps_in_windows(synthetic_data, window_size=5)
        assert len(result) == 1
        assert result[0] == 0.5

class TestLoadPrimesGaps:
    def test_load_from_temp_file(self):
        content = "prime_before,prime_after,gap_size,normalized_gap\n10,12,2,0.1\n12,14,2,0.2\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)
        
        try:
            data = load_primes_gaps(temp_path)
            assert len(data) == 2
            assert data[0] == (10, 12, 2, 0.1)
        finally:
            os.unlink(temp_path)

class TestPlotCdfComparison:
    def test_plot_generation(self):
        import tempfile
        data = [1.0, 2.0, 3.0, 4.0, 5.0]
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_plot.png"
            plot_cdf_comparison(data, output_path)
            assert output_path.exists()
            assert output_path.stat().st_size > 0
