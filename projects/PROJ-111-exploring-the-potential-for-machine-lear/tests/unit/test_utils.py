"""
Unit tests for code/utils.py functions.
Specifically verifies the magnetic susceptibility calculation against
a known analytical/numerical result for a small lattice.
"""
import unittest
import numpy as np
import sys
import os

# Ensure the code directory is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils import calculate_magnetic_susceptibility

class TestMagneticSusceptibility(unittest.TestCase):
    """Tests for the calculate_magnetic_susceptibility function."""

    def test_known_analytical_result_small_lattice(self):
        """
        Verify susceptibility calculation against a known result for a 2x2 Ising-like
        configuration (simplified 2D case) where we can manually compute M and M^2.

        For a 2x2 lattice (N=4) with spins:
        [[1, 1],
         [1, 1]]
        Magnetization M = sum(spin) = 4.
        |M| = 4.
        M^2 = 16.
        Variance of M (for a single configuration treated as a sample from a distribution
        where this is the only state, or simply checking the formula implementation):
        The formula in utils is: chi = (M^2 - |M|^2) / N.
        Wait, the formula in the prompt description is: chi = 1/N * (<M^2> - <|M>|^2).
        
        If we have a single configuration (or a dataset of identical configurations):
        <M^2> = 16
        <|M|> = 4 -> <|M|>^2 = 16
        chi = (16 - 16) / 4 = 0.
        
        Let's test with a configuration that has non-zero variance if we consider
        a small set of configurations, OR simply verify the arithmetic for a single
        configuration where the formula should yield 0 if M is constant.
        
        However, the standard definition for susceptibility in Monte Carlo is:
        chi = (1/(N*T)) * ( <M^2> - <M>^2 )  (for M = sum spins)
        OR using absolute magnetization:
        chi = (1/N) * ( <M^2> - <|M|>^2 )
        
        Let's construct a small batch of configurations to test the variance logic.
        Batch:
        Config 1: All +1 (M=4)
        Config 2: All -1 (M=-4)
        
        If we pass a stack of these two:
        Spins shape: (2, 2, 2) -> 2 samples, 2x2 lattice.
        M1 = 4, M2 = -4.
        <M^2> = (16 + 16) / 2 = 16.
        <|M|> = (4 + 4) / 2 = 4.
        <|M|>^2 = 16.
        Expected chi = (16 - 16) / 4 = 0.
        
        Let's try a case with actual variance in |M|.
        Config 1: All +1 (M=4, |M|=4)
        Config 2: 3 up, 1 down (M=2, |M|=2)
        
        Batch:
        [
          [[1, 1], [1, 1]],  -> M=4
          [[1, 1], [1, -1]]  -> M=2
        ]
        
        <M^2> = (16 + 4) / 2 = 10.
        <|M|> = (4 + 2) / 2 = 3.
        <|M|>^2 = 9.
        Expected chi = (10 - 9) / 4 = 0.25.
        """
        
        # Create a 2x2 lattice batch
        # Shape: (batch_size, L, L)
        spins = np.array([
            [[1.0, 1.0], [1.0, 1.0]],  # M = 4
            [[1.0, 1.0], [1.0, -1.0]]  # M = 2
        ], dtype=np.float64)
        
        # Call the function
        chi = calculate_magnetic_susceptibility(spins)
        
        # Calculate expected manually
        # M vector
        M_vec = np.sum(spins, axis=(1, 2)) # [4.0, 2.0]
        M_sq = M_vec ** 2                  # [16.0, 4.0]
        abs_M = np.abs(M_vec)              # [4.0, 2.0]
        
        mean_M_sq = np.mean(M_sq)          # 10.0
        mean_abs_M = np.mean(abs_M)        # 3.0
        mean_abs_M_sq = mean_abs_M ** 2    # 9.0
        
        N = spins.shape[1] * spins.shape[2] # 4
        expected_chi = (mean_M_sq - mean_abs_M_sq) / N # (10 - 9) / 4 = 0.25
        
        self.assertAlmostEqual(chi, expected_chi, places=6, 
                               msg=f"Calculated chi={chi}, expected {expected_chi}")

    def test_constant_magnetization(self):
        """
        Test that if |M| is constant across the batch, chi is 0.
        """
        spins = np.array([
            [[1.0, 1.0], [1.0, 1.0]],  # M=4
            [[-1.0, -1.0], [-1.0, -1.0]] # M=-4, |M|=4
        ], dtype=np.float64)
        
        chi = calculate_magnetic_susceptibility(spins)
        
        # <M^2> = (16+16)/2 = 16
        # <|M|> = (4+4)/2 = 4 -> 16
        # chi = 0
        self.assertAlmostEqual(chi, 0.0, places=6)

    def test_shape_handling(self):
        """
        Ensure the function handles standard input shapes correctly.
        """
        L = 4
        batch_size = 10
        spins = np.random.randn(batch_size, L, L)
        
        chi = calculate_magnetic_susceptibility(spins)
        
        self.assertIsInstance(chi, float)
        self.assertTrue(np.isfinite(chi))

if __name__ == '__main__':
    unittest.main()