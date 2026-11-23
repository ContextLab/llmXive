"""
Unit test for T094: Permutation Test Determinism Check.

This test verifies that the permutation test logic in `code/statistical_test.py`
produces identical null distributions across multiple runs when initialized
with the same random seed. This ensures the "within-language similarity" baseline
is reproducible and not affected by RNG state drift.
"""
import json
import os
import tempfile
import numpy as np
import pytest
from pathlib import Path

# Import the function under test from the existing API surface
from statistical_test import generate_null_distribution, calculate_p_value, run_statistical_test


class TestPermutationDeterminism:
    """Tests for ensuring deterministic behavior in permutation tests."""

    @pytest.fixture
    def sample_similarity_data(self):
        """Generate a fixed, deterministic sample similarity dataset."""
        # Create a deterministic dataset based on known values
        np.random.seed(42)
        n_samples = 100
        
        # Simulate within-language similarities (null distribution source)
        within_lang_sim = np.random.normal(loc=0.85, scale=0.05, size=n_samples)
        
        # Simulate cross-lingual similarities (observed)
        cross_lang_sim = np.random.normal(loc=0.65, scale=0.05, size=50)
        
        data = {
            "within_language_similarities": within_lang_sim.tolist(),
            "cross_language_similarities": cross_lang_sim.tolist(),
            "metadata": {
                "source": "test_fixtures",
                "n_within": n_samples,
                "n_cross": 50
            }
        }
        return data

    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for output files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_null_distribution_determinism(self, sample_similarity_data, temp_output_dir):
        """
        Test that generate_null_distribution produces identical results 
        across runs with the same seed.
        """
        # Save sample data to a temp file
        data_path = Path(temp_output_dir) / "similarity_data.json"
        with open(data_path, "w") as f:
            json.dump(sample_similarity_data, f)

        # Define a fixed seed
        fixed_seed = 12345
        n_permutations = 50  # Small number for speed
        
        # Run the first time
        results_1 = run_statistical_test(
            similarity_file=str(data_path),
            output_file=str(Path(temp_output_dir) / "results_1.json"),
            n_permutations=n_permutations,
            seed=fixed_seed
        )

        # Run the second time with the exact same seed
        results_2 = run_statistical_test(
            similarity_file=str(data_path),
            output_file=str(Path(temp_output_dir) / "results_2.json"),
            n_permutations=n_permutations,
            seed=fixed_seed
        )

        # Verify that the null distributions are bitwise identical
        # The null distribution is the core of the permutation test
        null_dist_1 = results_1.get("null_distribution", [])
        null_dist_2 = results_2.get("null_distribution", [])

        assert len(null_dist_1) == len(null_dist_2), \
            f"Null distribution lengths differ: {len(null_dist_1)} vs {len(null_dist_2)}"

        # Convert to numpy arrays for numerical comparison
        arr_1 = np.array(null_dist_1)
        arr_2 = np.array(null_dist_2)

        # Check for exact equality (deterministic requirement)
        assert np.array_equal(arr_1, arr_2), \
            "Null distributions are not identical across runs with the same seed."

        # Also verify that other derived metrics are identical
        assert results_1["p_value"] == results_2["p_value"], \
            f"P-values differ: {results_1['p_value']} vs {results_2['p_value']}"
        
        assert results_1["observed_similarity"] == results_2["observed_similarity"], \
            "Observed similarities differ."

    def test_permutation_logic_seed_isolation(self, temp_output_dir):
        """
        Test that running two different seeds produces different results,
        confirming that the seed actually controls the RNG state.
        """
        # Create a minimal mock data file
        data = {
            "within_language_similarities": [0.8, 0.82, 0.79, 0.81, 0.83],
            "cross_language_similarities": [0.6, 0.62, 0.59],
            "metadata": {"test": True}
        }
        data_path = Path(temp_output_dir) / "mock_data.json"
        with open(data_path, "w") as f:
            json.dump(data, f)

        # Run with seed A
        res_a = run_statistical_test(
            similarity_file=str(data_path),
            output_file=str(Path(temp_output_dir) / "res_a.json"),
            n_permutations=20,
            seed=100
        )

        # Run with seed B
        res_b = run_statistical_test(
            similarity_file=str(data_path),
            output_file=str(Path(temp_output_dir) / "res_b.json"),
            n_permutations=20,
            seed=200
        )

        # They should likely be different (probabilistic nature)
        # We check that they are NOT bitwise identical to confirm seed isolation
        null_a = np.array(res_a["null_distribution"])
        null_b = np.array(res_b["null_distribution"])

        # With different seeds, the distributions should differ (high probability)
        # If they happen to be identical by extreme chance, the test might pass incorrectly,
        # but with n=20 and normal distribution, this is negligible.
        if np.array_equal(null_a, null_b):
            # If they are equal, check p-values
            assert res_a["p_value"] != res_b["p_value"], \
                "Results for different seeds are identical, suggesting seed isolation failure."
        else:
            # This is the expected path
            pass

    def test_generate_null_distribution_direct(self):
        """
        Direct test of generate_null_distribution with fixed seed.
        """
        # Create synthetic within-language data
        np.random.seed(999)
        within_data = np.random.normal(0.8, 0.05, 50).tolist()
        
        # Simulate a perturbation function (mocking the logic inside statistical_test)
        # We rely on the function to use the global seed or passed seed
        
        seed = 5555
        n_iter = 30
        
        # Run 1
        dist_1 = generate_null_distribution(
            within_similarities=within_data,
            n_permutations=n_iter,
            seed=seed
        )
        
        # Run 2
        dist_2 = generate_null_distribution(
            within_similarities=within_data,
            n_permutations=n_iter,
            seed=seed
        )
        
        # Verify identity
        assert len(dist_1) == len(dist_2) == n_iter
        assert np.allclose(dist_1, dist_2), \
            "generate_null_distribution is not deterministic with fixed seed."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
