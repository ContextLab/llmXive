"""
Unit tests for permutation test logic and null distribution generation.
Implements T035: Verify null distribution generation in permutation tests.
"""
import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.evaluation import run_permutation_test, calculate_p_value
from utils.logging import get_module_logger


class TestPermutationLogicT035(unittest.TestCase):
    """
    Test suite for permutation test logic (T035).
    Verifies that null distributions are generated correctly and
    that the statistical properties hold for known inputs.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.logger = get_module_logger(__name__)
        self.temp_dir = tempfile.mkdtemp()
        self.data_path = Path(self.temp_dir) / "test_data.csv"

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_dataset(self, n_samples=100, n_features=5, signal_strength=0.0):
        """
        Create a synthetic dataset for testing.
        
        Args:
            n_samples: Number of samples
            n_features: Number of features
            signal_strength: Strength of the signal (0.0 = pure noise)
        
        Returns:
            pd.DataFrame: Test dataset
        """
        np.random.seed(42)
        X = np.random.randn(n_samples, n_features)
        
        if signal_strength > 0:
            # Create a known linear relationship
            true_coefs = np.array([signal_strength, 0, 0, 0, 0])
            y = X @ true_coefs + np.random.randn(n_samples) * 0.5
        else:
            # Pure noise
            y = np.random.randn(n_samples)
        
        df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(n_features)])
        df["target"] = y
        return df

    def test_null_distribution_generation_no_signal(self):
        """
        Verify that when there is no signal, the null distribution
        centers around zero and produces high p-values.
        
        This is the core test for T035: verifying the null distribution
        generation logic works correctly.
        """
        # Create dataset with NO signal (pure noise)
        df = self._create_test_dataset(n_samples=50, n_features=3, signal_strength=0.0)
        df.to_csv(self.data_path, index=False)

        # Run permutation test with small n for speed
        n_permutations = 100  # Small for unit test speed
        
        result = run_permutation_test(
            data_path=str(self.data_path),
            target_col="target",
            n_permutations=n_permutations,
            random_seed=42,
            output_dir=self.temp_dir
        )

        # Assertions for T035: Null distribution logic
        self.assertIn("null_distribution", result)
        self.assertIn("observed_r2", result)
        self.assertIn("p_value", result)
        
        null_dist = result["null_distribution"]
        
        # The null distribution should have exactly n_permutations values
        self.assertEqual(len(null_dist), n_permutations)
        
        # For pure noise, the mean of the null distribution should be near zero
        # (allowing for some sampling variance)
        self.assertAlmostEqual(np.mean(null_dist), 0.0, delta=0.1)
        
        # The p-value should be high (indicating no significant signal)
        # With pure noise, p-value should typically be > 0.05
        self.assertGreater(result["p_value"], 0.01)

    def test_null_distribution_with_signal(self):
        """
        Verify that when there IS a signal, the observed R2 is significantly
        higher than the null distribution, producing a low p-value.
        """
        # Create dataset WITH signal
        df = self._create_test_dataset(n_samples=100, n_features=3, signal_strength=1.0)
        df.to_csv(self.data_path, index=False)

        n_permutations = 200
        
        result = run_permutation_test(
            data_path=str(self.data_path),
            target_col="target",
            n_permutations=n_permutations,
            random_seed=42,
            output_dir=self.temp_dir
        )

        # Assertions for T035: Null distribution logic
        self.assertIn("null_distribution", result)
        self.assertIn("observed_r2", result)
        self.assertIn("p_value", result)
        
        null_dist = result["null_distribution"]
        observed_r2 = result["observed_r2"]
        
        # The null distribution should have exactly n_permutations values
        self.assertEqual(len(null_dist), n_permutations)
        
        # The observed R2 should be significantly higher than the null distribution
        # (i.e., greater than the 95th percentile of the null)
        self.assertGreater(observed_r2, np.percentile(null_dist, 95))
        
        # The p-value should be low (indicating significant signal)
        self.assertLess(result["p_value"], 0.1)  # Relaxed for small sample

    def test_deterministic_permutation_with_seed(self):
        """
        Verify that permutation tests are deterministic when a seed is provided.
        This ensures the null distribution generation is reproducible.
        """
        df = self._create_test_dataset(n_samples=50, n_features=3, signal_strength=0.5)
        df.to_csv(self.data_path, index=False)

        n_permutations = 50
        
        # Run twice with the same seed
        result1 = run_permutation_test(
            data_path=str(self.data_path),
            target_col="target",
            n_permutations=n_permutations,
            random_seed=123,
            output_dir=self.temp_dir
        )

        result2 = run_permutation_test(
            data_path=str(self.data_path),
            target_col="target",
            n_permutations=n_permutations,
            random_seed=123,
            output_dir=self.temp_dir
        )

        # Verify determinism for T035
        self.assertEqual(result1["observed_r2"], result2["observed_r2"])
        self.assertEqual(result1["p_value"], result2["p_value"])
        np.testing.assert_array_equal(
            result1["null_distribution"], 
            result2["null_distribution"],
            err_msg="Null distributions should be identical with same seed"
        )

    def test_p_value_calculation_edge_cases(self):
        """
        Test p-value calculation logic for edge cases.
        """
        # Case 1: Observed value is the maximum in null distribution
        null_dist = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        observed = 0.6
        p_val = calculate_p_value(observed, null_dist)
        # p-value = (count >= observed + 1) / (n + 1) = (0 + 1) / 6 = 0.166...
        expected_p = 1.0 / (len(null_dist) + 1)
        self.assertAlmostEqual(p_val, expected_p)

        # Case 2: Observed value is the minimum
        observed = 0.0
        p_val = calculate_p_value(observed, null_dist)
        # All values are >= observed, so (5 + 1) / 6 = 1.0
        self.assertAlmostEqual(p_val, 1.0)

        # Case 3: Observed value is in the middle
        observed = 0.25
        p_val = calculate_p_value(observed, null_dist)
        # Values >= 0.25: [0.3, 0.4, 0.5] -> count = 3
        # p = (3 + 1) / 6 = 0.666...
        expected_p = 4.0 / 6.0
        self.assertAlmostEqual(p_val, expected_p)

    def test_null_distribution_shape(self):
        """
        Verify that the null distribution approximates a normal distribution
        for large N, as expected by the Central Limit Theorem.
        """
        df = self._create_test_dataset(n_samples=200, n_features=5, signal_strength=0.0)
        df.to_csv(self.data_path, index=False)

        n_permutations = 1000
        
        result = run_permutation_test(
            data_path=str(self.data_path),
            target_col="target",
            n_permutations=n_permutations,
            random_seed=42,
            output_dir=self.temp_dir
        )

        null_dist = result["null_distribution"]
        
        # For large N, the null distribution should be approximately normal
        # Check skewness is close to 0
        skewness = pd.Series(null_dist).skew()
        self.assertLess(abs(skewness), 0.5, "Null distribution should be approximately symmetric")

        # Check kurtosis is close to 3 (normal distribution)
        kurtosis = pd.Series(null_dist).kurtosis() + 3
        self.assertGreater(kurtosis, 2.0)
        self.assertLess(kurtosis, 4.0)

    def test_permutation_test_output_file(self):
        """
        Verify that the permutation test saves results to disk correctly.
        """
        df = self._create_test_dataset(n_samples=50, n_features=3, signal_strength=0.0)
        df.to_csv(self.data_path, index=False)

        n_permutations = 50
        output_file = Path(self.temp_dir) / "permutation_results.json"
        
        result = run_permutation_test(
            data_path=str(self.data_path),
            target_col="target",
            n_permutations=n_permutations,
            random_seed=42,
            output_dir=self.temp_dir
        )

        # Verify file was created
        self.assertTrue(output_file.exists(), "Permutation results file should be created")

        # Verify file contains expected data
        import json
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        
        self.assertIn("observed_r2", saved_data)
        self.assertIn("p_value", saved_data)
        self.assertIn("null_distribution", saved_data)
        self.assertEqual(len(saved_data["null_distribution"]), n_permutations)


if __name__ == "__main__":
    unittest.main()