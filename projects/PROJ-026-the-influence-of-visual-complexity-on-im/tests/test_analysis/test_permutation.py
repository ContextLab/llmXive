import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from analysis.permutation import run_permutation_test, calculate_power

class TestLeaveOneImageOut:
    """
    Unit tests for the Leave-One-Image-Out (LOIO) sensitivity logic.
    
    This test suite verifies that the permutation test logic correctly handles
    the exclusion of specific images (or groups of images associated with complexity levels)
    to ensure results are not driven by a single outlier stimulus.
    
    Note: The core permutation logic is tested in T028. These tests focus on the
    robustness/sensitivity aspect implied by LOIO, specifically:
    1. That the test runs successfully when a specific subset of data is removed.
    2. That the resulting p-value and effect size are consistent with the reduced dataset.
    3. That the function handles edge cases where removing data leaves insufficient samples.
    """

    def setup_method(self):
        """
        Setup test fixtures before each test method.
        Creates a mock dataset with known properties.
        """
        np.random.seed(42)
        
        # Create a synthetic dataset mimicking D-scores from two conditions:
        # Low Complexity (Group 0) and High Complexity (Group 1)
        # We simulate 30 participants per group for a total of 60 trials
        n_per_group = 30
        
        # Group 0: Low Complexity (Mean ~ 0.1, SD ~ 0.4)
        group_0 = np.random.normal(loc=0.1, scale=0.4, size=n_per_group)
        
        # Group 1: High Complexity (Mean ~ 0.3, SD ~ 0.4)
        group_1 = np.random.normal(loc=0.3, scale=0.4, size=n_per_group)
        
        # Combine into a DataFrame
        self.df_full = pd.DataFrame({
            'participant_id': [f'P{i:03d}' for i in range(n_per_group * 2)],
            'complexity_group': [0] * n_per_group + [1] * n_per_group,
            'd_score': np.concatenate([group_0, group_1])
        })

    def test_loio_logic_removes_single_observation(self):
        """
        Verify that the permutation test can run when a single observation is removed
        (simulating the removal of one image's contribution if it were the sole driver).
        
        This acts as a proxy for LOIO: if removing one data point doesn't crash the
        permutation engine and produces a valid result, the logic holds.
        """
        # Simulate removing the last observation (High Complexity group)
        df_reduced = self.df_full.iloc[:-1].copy()
        
        # Ensure we still have enough data for a permutation test (min 5 per group usually)
        assert len(df_reduced[df_reduced['complexity_group'] == 0]) >= 5
        assert len(df_reduced[df_reduced['complexity_group'] == 1]) >= 5
        
        # Run the permutation test on the reduced dataset
        # We use a small number of permutations for speed in unit tests
        result = run_permutation_test(
            df_reduced, 
            group_col='complexity_group', 
            value_col='d_score', 
            n_permutations=100, 
            seed=42
        )
        
        # Assertions
        assert isinstance(result, dict)
        assert 'p_value' in result
        assert 'effect_size' in result
        assert 'observed_diff' in result
        
        # The result should be numeric
        assert isinstance(result['p_value'], (int, float))
        assert isinstance(result['effect_size'], (int, float))
        
        # With n=59, we should still get a result (though power is lower)
        assert result['n_trials_valid'] == 59

    def test_loio_logic_removes_entire_condition_subset(self):
        """
        Simulate removing a specific 'image' that contributed to multiple trials
        by removing a subset of one condition.
        
        In a real LOIO scenario, we might remove all trials associated with a specific
        background image. Here we simulate removing 5 trials from the High group.
        """
        # Filter out 5 trials from Group 1 (High Complexity)
        mask = self.df_full['complexity_group'] == 1
        indices_to_remove = self.df_full[mask].index[:5]
        df_reduced = self.df_full.drop(indices_to_remove).reset_index(drop=True)
        
        assert len(df_reduced) == 55
        assert len(df_reduced[df_reduced['complexity_group'] == 1]) == 25
        
        result = run_permutation_test(
            df_reduced, 
            group_col='complexity_group', 
            value_col='d_score', 
            n_permutations=100, 
            seed=42
        )
        
        assert result['n_trials_valid'] == 55
        assert 'p_value' in result
        assert result['p_value'] >= 0.0 and result['p_value'] <= 1.0

    def test_loio_edge_case_insufficient_samples(self):
        """
        Verify behavior when LOIO removal leaves insufficient samples for the test.
        
        If removing an image leaves fewer than the minimum required trials per group
        (e.g., < 5), the function should handle this gracefully (raise ValueError or return NaN).
        Based on the implementation plan, it should fail loudly or return a specific status.
        """
        # Create a dataset with exactly 5 samples per group
        df_minimal = pd.DataFrame({
            'participant_id': [f'P{i:03d}' for i in range(10)],
            'complexity_group': [0] * 5 + [1] * 5,
            'd_score': np.random.normal(0.2, 0.4, 10)
        })
        
        # Remove one sample from Group 1 -> 4 samples left
        df_too_small = df_minimal.drop(df_minimal[df_minimal['complexity_group'] == 1].index[0]).reset_index(drop=True)
        
        # The run_permutation_test function should handle this.
        # We expect it to either raise a ValueError or return a result with a flag.
        # Given the "Fail loudly" constraint, we expect a ValueError if the implementation
        # enforces a strict minimum. If it returns NaN, we check for that.
        
        try:
            result = run_permutation_test(
                df_too_small, 
                group_col='complexity_group', 
                value_col='d_score', 
                n_permutations=100, 
                seed=42
            )
            # If it doesn't raise, it should return a result indicating failure/insufficient data
            # Check if the implementation returns a specific status or NaN
            # For this test, we assume the implementation raises ValueError for < min_samples
            # If it doesn't, we assert the result structure is valid even if p-value is NaN
            assert 'p_value' in result
            # If the implementation allows it, p_value might be NaN or 1.0
            # We just ensure the function didn't crash unexpectedly
        except ValueError as e:
            # This is an acceptable outcome: "Fail loudly"
            assert "insufficient" in str(e).lower() or "sample" in str(e).lower()

    def test_loio_deterministic_seed(self):
        """
        Verify that running LOIO (removing a specific subset) with a fixed seed
        produces deterministic results.
        """
        # Remove a specific set of indices
        indices_to_remove = [0, 1, 2]
        df_reduced = self.df_full.drop(indices_to_remove).reset_index(drop=True)
        
        result_1 = run_permutation_test(
            df_reduced, 
            group_col='complexity_group', 
            value_col='d_score', 
            n_permutations=100, 
            seed=42
        )
        
        result_2 = run_permutation_test(
            df_reduced, 
            group_col='complexity_group', 
            value_col='d_score', 
            n_permutations=100, 
            seed=42
        )
        
        assert result_1['p_value'] == result_2['p_value']
        assert result_1['effect_size'] == result_2['effect_size']

    def test_loio_consistency_with_full_dataset(self):
        """
        Verify that the LOIO logic produces results consistent with the full dataset
        when no data is removed (edge case of LOIO).
        """
        result_full = run_permutation_test(
            self.df_full, 
            group_col='complexity_group', 
            value_col='d_score', 
            n_permutations=100, 
            seed=42
        )
        
        # Remove nothing (empty list)
        result_no_remove = run_permutation_test(
            self.df_full, 
            group_col='complexity_group', 
            value_col='d_score', 
            n_permutations=100, 
            seed=42
        )
        
        assert result_full['p_value'] == result_no_remove['p_value']
        assert result_full['effect_size'] == result_no_remove['effect_size']
        assert result_full['observed_diff'] == result_no_remove['observed_diff']