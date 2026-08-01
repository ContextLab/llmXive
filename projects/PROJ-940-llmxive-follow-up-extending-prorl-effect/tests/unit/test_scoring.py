"""
Unit tests for the ProRL Position-Specific Advantage (PSA) formula.

This module tests the PSA rectification logic defined in src/path_generator.py.
The PSA formula is: S_final = S_rect * (1 + alpha * pos)

Where:
- S_rect: Stepwise Reward Centered score (S_raw - mu_batch)
- alpha: The path length sensitivity parameter (default 0.1)
- pos: The 0-indexed position in the path
"""
import pytest
import numpy as np
from src.path_generator import apply_prorl_rectification
from src.entities import RecommendationPath


class TestPSAFormula:
    """Test suite for the Position-Specific Advantage (PSA) component of ProRL."""

    def test_psa_zero_position(self):
        """
        Test that at position 0, the multiplier is 1.0 (1 + alpha * 0).
        The score should be equal to the rectified score (S_rect).
        """
        # Create a mock path with a single node at position 0
        # We simulate the input to apply_prorl_rectification
        # The function expects a list of paths or a single path object
        # Let's construct a simple scenario to test the math directly via the function
        
        # Mock data: 1 path, 1 step (pos 0)
        # S_raw = 0.8, mu_batch = 0.8 -> S_rect = 0.0
        # Expected S_final = 0.0 * (1 + 0.1 * 0) = 0.0
        
        paths = [
            RecommendationPath(
                seed_id="seed_1",
                path_items=["item_1"],
                raw_scores=[0.8],
                rectified_scores=None,  # Will be calculated
                final_scores=None       # Will be calculated
            )
        ]
        
        # Run rectification
        result = apply_prorl_rectification(paths, alpha=0.1)
        
        # At pos 0: multiplier = 1.0
        # S_rect = 0.8 - 0.8 = 0.0
        # S_final should be 0.0
        assert np.isclose(result[0].final_scores[0], 0.0, atol=1e-6)

    def test_psa_positive_alpha(self):
        """
        Test that with positive alpha, scores increase with position.
        S_final = S_rect * (1 + alpha * pos)
        """
        alpha = 0.1
        # Create a path of length 3 (positions 0, 1, 2)
        # Assume S_rect is constant 1.0 for all steps to isolate the multiplier effect
        # In reality, S_rect varies, but we can control inputs if we mock S_rect directly
        # However, apply_prorl_rectification calculates S_rect from S_raw.
        # To isolate the PSA multiplier, we need S_raw such that S_rect is constant.
        # If mu_batch is the mean of S_raw, we can't easily force S_rect to be constant
        # unless all S_raw are the same.
        
        # Let's set all S_raw to 1.0. Then mu_batch = 1.0.
        # S_rect = 1.0 - 1.0 = 0.0. This results in 0.0 everywhere.
        # We need S_rect to be non-zero.
        
        # Strategy: Set S_raw such that S_rect is a known value.
        # If we set S_raw = [1.1, 1.1, 1.1], mu = 1.1, S_rect = 0.0.
        # If we set S_raw = [1.0, 1.0, 1.0], mu = 1.0, S_rect = 0.0.
        
        # Let's try a single path where we can calculate the expected outcome manually.
        # Path: [A, B, C]
        # S_raw = [0.9, 0.9, 0.9] -> mu = 0.9 -> S_rect = [0, 0, 0] -> S_final = 0.
        # We need S_raw to vary to get non-zero S_rect, but we want to test the multiplier.
        
        # Alternative: Test the multiplier logic directly by checking the ratio.
        # S_final[pos] / S_rect[pos] should be (1 + alpha * pos).
        
        # Let's construct a case where S_rect is non-zero.
        # S_raw = [0.8, 0.9, 1.0]
        # mu = (0.8 + 0.9 + 1.0) / 3 = 2.7 / 3 = 0.9
        # S_rect = [0.8-0.9, 0.9-0.9, 1.0-0.9] = [-0.1, 0.0, 0.1]
        
        paths = [
            RecommendationPath(
                seed_id="seed_1",
                path_items=["A", "B", "C"],
                raw_scores=[0.8, 0.9, 1.0],
                rectified_scores=None,
                final_scores=None
            )
        ]
        
        result = apply_prorl_rectification(paths, alpha=0.1)
        
        # Expected S_rect: [-0.1, 0.0, 0.1]
        # Expected Multipliers: [1.0, 1.1, 1.2]
        # Expected S_final:
        # pos 0: -0.1 * 1.0 = -0.1
        # pos 1: 0.0 * 1.1 = 0.0
        # pos 2: 0.1 * 1.2 = 0.12
        
        expected_final = [-0.1, 0.0, 0.12]
        
        for i, (calc, exp) in enumerate(zip(result[0].final_scores, expected_final)):
            assert np.isclose(calc, exp, atol=1e-6), f"Mismatch at pos {i}: {calc} vs {exp}"

    def test_psa_zero_alpha(self):
        """
        Test that with alpha=0, the score is just S_rect (multiplier is 1.0).
        S_final = S_rect * (1 + 0 * pos) = S_rect
        """
        alpha = 0.0
        paths = [
            RecommendationPath(
                seed_id="seed_1",
                path_items=["A", "B"],
                raw_scores=[0.8, 1.2],
                rectified_scores=None,
                final_scores=None
            )
        ]
        
        result = apply_prorl_rectification(paths, alpha=alpha)
        
        # mu = 1.0
        # S_rect = [-0.2, 0.2]
        # S_final should be same as S_rect
        expected_rectified = [-0.2, 0.2]
        
        for i, (calc, exp) in enumerate(zip(result[0].final_scores, expected_rectified)):
            assert np.isclose(calc, exp, atol=1e-6), f"Mismatch at pos {i}: {calc} vs {exp}"

    def test_psa_negative_alpha(self):
        """
        Test that with negative alpha, scores decrease with position (penalizing long paths).
        S_final = S_rect * (1 + alpha * pos)
        """
        alpha = -0.1
        # S_raw = [0.8, 0.9, 1.0] -> mu = 0.9 -> S_rect = [-0.1, 0.0, 0.1]
        paths = [
            RecommendationPath(
                seed_id="seed_1",
                path_items=["A", "B", "C"],
                raw_scores=[0.8, 0.9, 1.0],
                rectified_scores=None,
                final_scores=None
            )
        ]
        
        result = apply_prorl_rectification(paths, alpha=alpha)
        
        # Expected Multipliers: [1.0, 0.9, 0.8]
        # Expected S_final:
        # pos 0: -0.1 * 1.0 = -0.1
        # pos 1: 0.0 * 0.9 = 0.0
        # pos 2: 0.1 * 0.8 = 0.08
        
        expected_final = [-0.1, 0.0, 0.08]
        
        for i, (calc, exp) in enumerate(zip(result[0].final_scores, expected_final)):
            assert np.isclose(calc, exp, atol=1e-6), f"Mismatch at pos {i}: {calc} vs {exp}"

    def test_psa_multiple_paths(self):
        """
        Test that PSA is applied independently to multiple paths.
        Each path has its own mu_batch.
        """
        paths = [
            # Path 1: [0.5, 0.5, 0.5] -> mu=0.5, S_rect=[0,0,0] -> S_final=[0,0,0]
            RecommendationPath(
                seed_id="seed_1",
                path_items=["A", "B", "C"],
                raw_scores=[0.5, 0.5, 0.5],
                rectified_scores=None,
                final_scores=None
            ),
            # Path 2: [0.8, 0.9, 1.0] -> mu=0.9, S_rect=[-0.1, 0.0, 0.1]
            RecommendationPath(
                seed_id="seed_2",
                path_items=["X", "Y", "Z"],
                raw_scores=[0.8, 0.9, 1.0],
                rectified_scores=None,
                final_scores=None
            )
        ]
        
        result = apply_prorl_rectification(paths, alpha=0.1)
        
        # Path 1
        assert all(np.isclose(s, 0.0, atol=1e-6) for s in result[0].final_scores)
        
        # Path 2: Same as test_psa_positive_alpha
        expected_path2 = [-0.1, 0.0, 0.12]
        for i, (calc, exp) in enumerate(zip(result[1].final_scores, expected_path2)):
            assert np.isclose(calc, exp, atol=1e-6), f"Path 2 Mismatch at pos {i}: {calc} vs {exp}"

    def test_psa_long_path(self):
        """
        Test PSA with a longer path (L=5) to ensure the formula holds for larger indices.
        """
        alpha = 0.1
        # S_raw = [0.6, 0.7, 0.8, 0.9, 1.0]
        # mu = 4.0 / 5 = 0.8
        # S_rect = [-0.2, -0.1, 0.0, 0.1, 0.2]
        raw_scores = [0.6, 0.7, 0.8, 0.9, 1.0]
        paths = [
            RecommendationPath(
                seed_id="seed_1",
                path_items=["A", "B", "C", "D", "E"],
                raw_scores=raw_scores,
                rectified_scores=None,
                final_scores=None
            )
        ]
        
        result = apply_prorl_rectification(paths, alpha=alpha)
        
        # Expected Multipliers: [1.0, 1.1, 1.2, 1.3, 1.4]
        # Expected S_final:
        # 0: -0.2 * 1.0 = -0.2
        # 1: -0.1 * 1.1 = -0.11
        # 2: 0.0 * 1.2 = 0.0
        # 3: 0.1 * 1.3 = 0.13
        # 4: 0.2 * 1.4 = 0.28
        
        expected_final = [-0.2, -0.11, 0.0, 0.13, 0.28]
        
        for i, (calc, exp) in enumerate(zip(result[0].final_scores, expected_final)):
            assert np.isclose(calc, exp, atol=1e-6), f"Mismatch at pos {i}: {calc} vs {exp}"

    def test_psa_rectified_scores_field(self):
        """
        Verify that the rectified_scores field is also populated correctly.
        """
        paths = [
            RecommendationPath(
                seed_id="seed_1",
                path_items=["A", "B"],
                raw_scores=[0.8, 1.2],
                rectified_scores=None,
                final_scores=None
            )
        ]
        
        result = apply_prorl_rectification(paths, alpha=0.1)
        
        # mu = 1.0
        # S_rect = [-0.2, 0.2]
        expected_rectified = [-0.2, 0.2]
        
        for i, (calc, exp) in enumerate(zip(result[0].rectified_scores, expected_rectified)):
            assert np.isclose(calc, exp, atol=1e-6), f"Rectified mismatch at pos {i}: {calc} vs {exp}"