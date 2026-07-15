"""
Unit tests for the Monte Carlo simulation module (src/analysis/monte_carlo.py).

These tests verify:
- Cramér model prime generation
- Normalized gap computation
- Single simulation execution
- Full Monte Carlo pipeline
- Output file generation and structure
"""

import pytest
import os
import sys
import math
import tempfile
from pathlib import Path
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.monte_carlo import (
    generate_cramer_primes,
    compute_cramer_gaps,
    run_single_simulation,
    run_monte_carlo_simulation
)
from src.utils.seeds import get_rng


class TestGenerateCramerPrimes:
    """Tests for Cramér model prime generation."""

    def test_generates_primes(self):
        """Test that the function generates the requested number of pseudo-primes."""
        rng = get_rng(42, "test")
        num_primes = 100
        primes = generate_cramer_primes(num_primes, rng, 42)

        assert len(primes) == num_primes
        assert all(isinstance(p, int) for p in primes)
        assert all(p >= 2 for p in primes)

    def test_primes_are_sorted(self):
        """Test that generated pseudo-primes are in ascending order."""
        rng = get_rng(42, "test")
        primes = generate_cramer_primes(50, rng, 42)

        assert primes == sorted(primes)

    def test_reproducibility(self):
        """Test that the same seed produces the same sequence."""
        rng1 = get_rng(42, "test")
        rng2 = get_rng(42, "test")

        primes1 = generate_cramer_primes(100, rng1, 42)
        primes2 = generate_cramer_primes(100, rng2, 42)

        assert primes1 == primes2

    def test_small_seed(self):
        """Test with a very small number of primes."""
        rng = get_rng(42, "test")
        primes = generate_cramer_primes(5, rng, 42)

        assert len(primes) == 5
        # First few Cramér pseudo-primes should be small
        assert primes[0] >= 2


class TestComputeCramerGaps:
    """Tests for normalized maximal gap computation."""

    def test_computes_gaps_correctly(self):
        """Test basic gap computation."""
        # Simple test case: primes [2, 3, 5, 7, 11]
        primes = [2, 3, 5, 7, 11]
        window_size = 3

        gaps = compute_cramer_gaps(primes, window_size)

        # With window_size=3, we have windows: [2,3,5], [3,5,7], [5,7,11]
        # Window [2,3,5]: gaps are 1, 2 -> max=2, p_before=3 -> normalized = 2/log(3)^2
        # Window [3,5,7]: gaps are 2, 2 -> max=2, p_before=3 -> normalized = 2/log(3)^2
        # Window [5,7,11]: gaps are 2, 4 -> max=4, p_before=5 -> normalized = 4/log(5)^2

        assert len(gaps) == 3
        assert all(isinstance(g, float) for g in gaps)
        assert all(g > 0 for g in gaps)

    def test_empty_list(self):
        """Test with empty prime list."""
        gaps = compute_cramer_gaps([], 10)
        assert gaps == []

    def test_single_prime(self):
        """Test with only one prime."""
        gaps = compute_cramer_gaps([2], 10)
        assert gaps == []

    def test_window_larger_than_primes(self):
        """Test when window size exceeds number of primes."""
        primes = [2, 3, 5]
        gaps = compute_cramer_gaps(primes, 10)
        assert gaps == []

    def test_normalization_formula(self):
        """Test that normalization uses log^2(p) correctly."""
        primes = [100, 101, 103, 107]  # Small window
        window_size = 2

        gaps = compute_cramer_gaps(primes, window_size)

        # Manual calculation for first window [100, 101, 103]
        # Max gap is 2 (between 101 and 103), p_before = 101
        # Normalized = 2 / log(101)^2
        expected = 2.0 / (math.log(101) ** 2)

        assert abs(gaps[0] - expected) < 1e-10


class TestRunSingleSimulation:
    """Tests for single simulation execution."""

    def test_returns_ks_statistic(self):
        """Test that single simulation returns a valid KS statistic."""
        rng = get_rng(42, "test")
        ks_stat = run_single_simulation(1000, 50, rng, 42)

        assert isinstance(ks_stat, float)
        assert 0 <= ks_stat <= 1  # KS statistic is between 0 and 1

    def test_handles_small_samples(self):
        """Test behavior with small sample sizes."""
        rng = get_rng(42, "test")
        # Very small sample might not produce enough gaps
        ks_stat = run_single_simulation(10, 5, rng, 42)

        # Could be NaN if insufficient data
        assert isinstance(ks_stat, float)

    def test_reproducibility(self):
        """Test that same seed produces same KS statistic."""
        rng1 = get_rng(42, "test")
        rng2 = get_rng(42, "test")

        ks1 = run_single_simulation(500, 20, rng1, 42)
        ks2 = run_single_simulation(500, 20, rng2, 42)

        assert ks1 == ks2


class TestRunMonteCarloSimulation:
    """Tests for the full Monte Carlo pipeline."""

    def test_creates_output_file(self):
        """Test that the function creates the output JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_null.json"

            results = run_monte_carlo_simulation(
                num_simulations=10,
                num_primes=1000,
                window_size=50,
                master_seed=42,
                output_path=output_path
            )

            assert output_path.exists()
            assert results is not None

    def test_results_structure(self):
        """Test that results have the expected structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_null.json"

            results = run_monte_carlo_simulation(
                num_simulations=5,
                num_primes=500,
                window_size=20,
                master_seed=42,
                output_path=output_path
            )

            assert "parameters" in results
            assert "statistics" in results
            assert "null_distribution" in results
            assert "description" in results

            # Check parameter keys
            assert "num_simulations" in results["parameters"]
            assert "num_primes_per_simulation" in results["parameters"]
            assert "window_size" in results["parameters"]
            assert "master_seed" in results["parameters"]

            # Check statistics keys
            assert "mean_ks_statistic" in results["statistics"]
            assert "std_ks_statistic" in results["statistics"]
            assert "min_ks_statistic" in results["statistics"]
            assert "max_ks_statistic" in results["statistics"]
            assert "median_ks_statistic" in results["statistics"]

    def test_null_distribution_is_list(self):
        """Test that null_distribution is a list of floats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_null.json"

            results = run_monte_carlo_simulation(
                num_simulations=10,
                num_primes=500,
                window_size=20,
                master_seed=42,
                output_path=output_path
            )

            assert isinstance(results["null_distribution"], list)
            assert len(results["null_distribution"]) == 10
            assert all(isinstance(x, float) for x in results["null_distribution"])

    def test_statistics_are_reasonable(self):
        """Test that computed statistics are mathematically consistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_null.json"

            results = run_monte_carlo_simulation(
                num_simulations=20,
                num_primes=1000,
                window_size=50,
                master_seed=42,
                output_path=output_path
            )

            dist = results["null_distribution"]
            stats = results["statistics"]

            # Mean should be between min and max
            assert stats["min_ks_statistic"] <= stats["mean_ks_statistic"] <= stats["max_ks_statistic"]

            # All KS statistics should be in [0, 1]
            assert all(0 <= x <= 1 for x in dist)

            # Standard deviation should be non-negative
            assert stats["std_ks_statistic"] >= 0

    def test_reproducibility(self):
        """Test that same master seed produces same results."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            output_path1 = Path(tmpdir1) / "test_null1.json"
            results1 = run_monte_carlo_simulation(
                num_simulations=10,
                num_primes=500,
                window_size=20,
                master_seed=42,
                output_path=output_path1
            )

        with tempfile.TemporaryDirectory() as tmpdir2:
            output_path2 = Path(tmpdir2) / "test_null2.json"
            results2 = run_monte_carlo_simulation(
                num_simulations=10,
                num_primes=500,
                window_size=20,
                master_seed=42,
                output_path=output_path2
            )

        # Results should be identical
        assert results1["null_distribution"] == results2["null_distribution"]
        assert results1["statistics"] == results2["statistics"]

    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different results."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            output_path1 = Path(tmpdir1) / "test_null1.json"
            results1 = run_monte_carlo_simulation(
                num_simulations=10,
                num_primes=500,
                window_size=20,
                master_seed=42,
                output_path=output_path1
            )

        with tempfile.TemporaryDirectory() as tmpdir2:
            output_path2 = Path(tmpdir2) / "test_null2.json"
            results2 = run_monte_carlo_simulation(
                num_simulations=10,
                num_primes=500,
                window_size=20,
                master_seed=123,
                output_path=output_path2
            )

        # Results should be different
        assert results1["null_distribution"] != results2["null_distribution"]

    def test_large_simulation(self):
        """Test with a larger number of simulations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_null.json"

            results = run_monte_carlo_simulation(
                num_simulations=50,
                num_primes=2000,
                window_size=100,
                master_seed=42,
                output_path=output_path
            )

            assert len(results["null_distribution"]) == 50
            assert output_path.exists()


class TestIntegration:
    """Integration tests for the Monte Carlo module."""

    def test_end_to_end(self):
        """Test the complete pipeline from generation to output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "full_test.json"

            # Run a small simulation
            results = run_monte_carlo_simulation(
                num_simulations=5,
                num_primes=500,
                window_size=20,
                master_seed=42,
                output_path=output_path
            )

            # Verify file was created
            assert output_path.exists()

            # Verify file is valid JSON
            import json
            with open(output_path, 'r') as f:
                loaded = json.load(f)

            assert loaded == results

    def test_json_serialization(self):
        """Test that all results can be serialized to JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "json_test.json"

            results = run_monte_carlo_simulation(
                num_simulations=10,
                num_primes=500,
                window_size=20,
                master_seed=42,
                output_path=output_path
            )

            # If we got here without error, JSON serialization worked
            assert output_path.stat().st_size > 0
