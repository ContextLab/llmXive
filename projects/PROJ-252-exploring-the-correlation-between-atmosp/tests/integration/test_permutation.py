"""
Integration test for permutation test convergence (T020).

This test verifies that the permutation test implementation in code/analysis.py
correctly shuffles labels and generates a null distribution that converges
as the number of permutations increases, matching SC-001 criteria.

Prerequisites:
- T017 must have generated data/processed/master_dataset.csv
- code/analysis.py must implement the permutation test logic
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from analysis import run_permutation_test
from config import get_random_seed, get_processed_path, get_test_event_count


class TestPermutationConvergence:
    """Test suite for permutation test convergence."""

    @pytest.fixture(scope="class")
    def master_dataset_path(self):
        """Ensure master dataset exists before running tests."""
        path = Path(get_processed_path()) / "master_dataset.csv"
        if not path.exists():
            pytest.skip(
                f"Master dataset not found at {path}. "
                "Run User Story 1 (T017) first to generate the dataset."
            )
        return path

    @pytest.fixture(scope="class")
    def dataset(self, master_dataset_path):
        """Load the master dataset for testing."""
        return pd.read_csv(master_dataset_path)

    def test_permutation_test_runs_without_error(self, dataset):
        """Verify the permutation test executes without crashing."""
        # Use a small number of permutations for speed in testing
        n_permutations = 100
        seed = get_random_seed()
        
        result = run_permutation_test(
            df=dataset,
            n_permutations=n_permutations,
            random_seed=seed
        )
        
        assert result is not None, "Permutation test returned None"
        assert "observed_statistic" in result, "Missing observed_statistic in result"
        assert "p_value" in result, "Missing p_value in result"
        assert "null_distribution" in result, "Missing null_distribution in result"
        assert "convergence_check" in result, "Missing convergence_check in result"

    def test_null_distribution_shape(self, dataset):
        """Verify the null distribution has the expected shape."""
        n_permutations = 500
        seed = get_random_seed()
        
        result = run_permutation_test(
            df=dataset,
            n_permutations=n_permutations,
            random_seed=seed
        )
        
        null_dist = np.array(result["null_distribution"])
        
        # The null distribution should have exactly n_permutations elements
        assert len(null_dist) == n_permutations, (
            f"Null distribution length {len(null_dist)} does not match "
            f"requested {n_permutations} permutations"
        )

    def test_p_value_calculation_logic(self, dataset):
        """
        Verify p-value is calculated correctly:
        p = (count of null_stats >= observed_statistic + 1) / (n_permutations + 1)
        """
        n_permutations = 1000
        seed = get_random_seed()
        
        result = run_permutation_test(
            df=dataset,
            n_permutations=n_permutations,
            random_seed=seed
        )
        
        observed = result["observed_statistic"]
        null_dist = np.array(result["null_distribution"])
        p_value = result["p_value"]
        
        # Manual calculation of p-value
        expected_p = (np.sum(null_dist >= observed) + 1) / (n_permutations + 1)
        
        # Allow for floating point tolerance
        assert np.isclose(p_value, expected_p, atol=1e-9), (
            f"P-value {p_value} does not match expected {expected_p}"
        )

    def test_convergence_check(self, dataset):
        """
        Verify the convergence check mechanism works.
        As n_permutations increases, the p-value should stabilize.
        """
        seeds = [42, 123, 456]
        p_values = []
        
        for seed in seeds:
            # Run with small permutations
            result_small = run_permutation_test(
                df=dataset,
                n_permutations=100,
                random_seed=seed
            )
            p_small = result_small["p_value"]
            
            # Run with larger permutations
            result_large = run_permutation_test(
                df=dataset,
                n_permutations=2000,
                random_seed=seed
            )
            p_large = result_large["p_value"]
            
            # Store the difference
            p_values.append(abs(p_small - p_large))
        
        # The p-values from small vs large permutations should be within tolerance
        # (Note: some variance is expected due to randomness, but it shouldn't be huge)
        max_diff = max(p_values)
        # If the difference is > 0.1, it suggests non-convergence or instability
        assert max_diff < 0.15, (
            f"Convergence check failed. Max p-value difference between "
            f"100 and 2000 permutations was {max_diff:.4f}. "
            f"This suggests the null distribution is not stabilizing."
        )

    def test_label_shuffling_effect(self, dataset):
        """
        Verify that shuffling labels actually changes the test statistic.
        If the null distribution is identical to the observed statistic,
        the shuffling might be broken.
        """
        n_permutations = 1000
        seed = get_random_seed()
        
        result = run_permutation_test(
            df=dataset,
            n_permutations=n_permutations,
            random_seed=seed
        )
        
        observed = result["observed_statistic"]
        null_dist = np.array(result["null_distribution"])
        
        # Calculate the proportion of null stats exactly equal to observed
        exact_matches = np.sum(null_dist == observed) / n_permutations
        
        # In a continuous KS test, exact matches should be rare unless
        # the data is extremely discrete. If > 50% match, shuffling might be broken.
        assert exact_matches < 0.5, (
            f"Too many null statistics ({exact_matches:.2%}) exactly match the "
            f"observed statistic ({observed:.4f}). This suggests the label "
            f"shuffling mechanism may not be working correctly."
        )

    def test_deterministic_with_seed(self, dataset):
        """
        Verify that running with the same seed produces identical results.
        """
        seed = 999
        n_permutations = 500
        
        result_1 = run_permutation_test(
            df=dataset,
            n_permutations=n_permutations,
            random_seed=seed
        )
        
        result_2 = run_permutation_test(
            df=dataset,
            n_permutations=n_permutations,
            random_seed=seed
        )
        
        assert result_1["p_value"] == result_2["p_value"], (
            "Results are not deterministic with the same seed."
        )
        assert result_1["null_distribution"] == result_2["null_distribution"], (
            "Null distributions are not deterministic with the same seed."
        )

    def test_result_structure_matches_spec(self, dataset):
        """
        Verify the output structure matches the expected format for
        downstream tasks (T023, T026).
        """
        n_permutations = 100
        seed = get_random_seed()
        
        result = run_permutation_test(
            df=dataset,
            n_permutations=n_permutations,
            random_seed=seed
        )
        
        required_keys = [
            "observed_statistic",
            "p_value",
            "null_distribution",
            "n_permutations",
            "random_seed",
            "convergence_check"
        ]
        
        for key in required_keys:
            assert key in result, f"Missing required key '{key}' in result"
        
        # Verify types
        assert isinstance(result["observed_statistic"], (int, float))
        assert isinstance(result["p_value"], (int, float))
        assert isinstance(result["null_distribution"], list)
        assert isinstance(result["n_permutations"], int)
        assert isinstance(result["random_seed"], int)
        assert isinstance(result["convergence_check"], dict)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
