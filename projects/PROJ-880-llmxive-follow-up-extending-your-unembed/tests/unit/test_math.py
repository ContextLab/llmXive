"""
Unit tests for mathematical operations in the llmXive pipeline.
Specifically tests for SVD extraction and Permutation logic.
"""
import unittest
import numpy as np
import torch
from pathlib import Path
import sys

# Add parent directory to path to allow imports from code/
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from config import load_config, get_seed
from model_analyzer import extract_svd_subspace
from statistical_test import generate_null_distribution, compute_p_value

class TestSVDExtraction(unittest.TestCase):
    """Tests for SVD extraction logic in model_analyzer.py"""

    def test_svd_extraction_rank_k(self):
        """Test that extract_svd_subspace returns exactly k singular vectors."""
        # Create a mock matrix (vocab_size x hidden_size)
        vocab_size = 1000
        hidden_size = 512
        k = 100
        
        # Use a fixed seed for reproducibility in testing
        np.random.seed(42)
        mock_matrix = np.random.randn(vocab_size, hidden_size).astype(np.float32)
        
        # Convert to torch tensor (as expected by model_analyzer)
        W_U = torch.tensor(mock_matrix)
        
        # Extract subspace
        U_k, S_k, V_k = extract_svd_subspace(W_U, k=k)
        
        # Assertions
        self.assertEqual(U_k.shape[1], k, "U matrix should have k columns")
        self.assertEqual(S_k.shape[0], k, "S vector should have k elements")
        self.assertEqual(V_k.shape[0], k, "V matrix should have k rows")
        
        # Verify orthogonality of U_k
        I = torch.matmul(U_k.T, U_k)
        self.assertTrue(torch.allclose(I, torch.eye(k), atol=1e-5), "U_k columns must be orthogonal")

    def test_svd_extraction_numerical_stability(self):
        """Test SVD extraction with rank-deficient matrix."""
        # Create a low-rank matrix
        m, n, r = 100, 100, 5
        A = np.random.randn(m, r).astype(np.float32) @ np.random.randn(r, n).astype(np.float32)
        W_U = torch.tensor(A)
        
        k = 10
        U_k, S_k, V_k = extract_svd_subspace(W_U, k=k)
        
        # Singular values beyond rank r should be near zero
        self.assertTrue(torch.all(S_k[r:] < 1e-5), "Singular values beyond rank should be negligible")

class TestPermutationLogic(unittest.TestCase):
    """Tests for permutation logic in statistical_test.py"""

    def test_permutation_fixed_seed_reproducibility(self):
        """
        Verify that generate_null_distribution produces identical results 
        when run with the same fixed seed.
        """
        # Setup parameters
        n_iterations = 50
        k = 10
        sigma = 0.01
        seed = 12345
        
        # Create a mock similarity score (observed value)
        observed_score = 0.85
        
        # Mock model weights (small matrix for speed)
        # Shape: (vocab_subset, hidden_dim)
        mock_weights = torch.randn(200, 50).float()
        
        # Run 1
        np.random.seed(seed)
        torch.manual_seed(seed)
        dist_1 = generate_null_distribution(
            mock_weights, 
            observed_score, 
            n_iterations=n_iterations, 
            k=k, 
            sigma=sigma
        )
        
        # Run 2 (reset seed to same value)
        np.random.seed(seed)
        torch.manual_seed(seed)
        dist_2 = generate_null_distribution(
            mock_weights, 
            observed_score, 
            n_iterations=n_iterations, 
            k=k, 
            sigma=sigma
        )
        
        # Assert distributions are identical
        self.assertTrue(np.allclose(dist_1, dist_2), 
                        "Null distribution must be reproducible with fixed seed")

    def test_permutation_distribution_shape(self):
        """Verify that the null distribution has the expected length."""
        n_iterations = 100
        seed = 42
        
        mock_weights = torch.randn(100, 20).float()
        observed_score = 0.5
        
        np.random.seed(seed)
        torch.manual_seed(seed)
        
        dist = generate_null_distribution(
            mock_weights, 
            observed_score, 
            n_iterations=n_iterations, 
            k=5, 
            sigma=0.01
        )
        
        self.assertEqual(len(dist), n_iterations, 
                         "Null distribution length must match n_iterations")

    def test_p_value_calculation(self):
        """Test p-value calculation logic for one-sided and two-sided tests."""
        observed = 0.9
        null_dist = np.array([0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1.0, 1.1])
        
        # One-sided test (greater than)
        p_val_greater = compute_p_value(observed, null_dist, alternative="greater")
        # In the array, only 1.0 and 1.1 are >= 0.9. Count = 2. Total = 10. p = 0.2
        expected_greater = 2 / len(null_dist)
        self.assertAlmostEqual(p_val_greater, expected_greater, places=5)
        
        # One-sided test (less than)
        p_val_less = compute_p_value(observed, null_dist, alternative="less")
        # In the array, 0.1..0.8 are < 0.9. Count = 8. Total = 10. p = 0.8
        expected_less = 8 / len(null_dist)
        self.assertAlmostEqual(p_val_less, expected_less, places=5)
        
        # Two-sided test
        # Distance from observed to mean of null
        null_mean = np.mean(null_dist)
        dist_obs = abs(observed - null_mean)
        # Count values where |x - mean| >= dist_obs
        # This is a simplified check; exact logic depends on implementation
        p_val_two = compute_p_value(observed, null_dist, alternative="two-sided")
        self.assertGreaterEqual(p_val_two, 0.0)
        self.assertLessEqual(p_val_two, 1.0)

    def test_permutation_weight_perturbation(self):
        """
        Verify that the null distribution generation actually perturbs weights
        and does not just return the original score.
        """
        seed = 999
        n_iterations = 20
        
        # Create a base weight matrix
        base_weights = torch.ones(50, 10).float() * 0.5
        observed_score = 0.6
        
        np.random.seed(seed)
        torch.manual_seed(seed)
        
        dist = generate_null_distribution(
            base_weights, 
            observed_score, 
            n_iterations=n_iterations, 
            k=3, 
            sigma=0.1  # Significant noise
        )
        
        # The perturbation should result in scores different from the observed
        # (unless by extreme chance, which is unlikely with sigma=0.1)
        # We check that the variance is non-zero
        self.assertGreater(np.var(dist), 1e-6, 
                           "Perturbation should introduce variance in scores")

if __name__ == "__main__":
    unittest.main()