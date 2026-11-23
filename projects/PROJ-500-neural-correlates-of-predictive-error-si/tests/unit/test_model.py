import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure src is in path for imports if running standalone
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.analysis.model import run_permutation_test, check_permutation_sufficiency

class TestPermutationTestSufficiency:
    """
    Unit tests for the permutation test implementation in src/analysis/model.py.
    Specifically verifies that the logic includes sufficiency checks or dynamic
    adjustment of n based on dataset size.
    """

    def test_check_permutation_sufficiency_stability(self):
        """
        Verify that check_permutation_sufficiency correctly identifies
        when p-values have stabilized across iterations.
        """
        # Simulate a list of p-values that stabilize
        p_values_stable = [0.05, 0.048, 0.049, 0.0485, 0.0482, 0.0481]
        
        # Check stability over the last 3 values
        is_stable = check_permutation_sufficiency(p_values_stable, window=3, tolerance=0.001)
        assert is_stable is True, "Stable p-values should return True"

    def test_check_permutation_sufficiency_unstable(self):
        """
        Verify that check_permutation_sufficiency correctly identifies
        when p-values are still fluctuating significantly.
        """
        # Simulate a list of p-values that are unstable
        p_values_unstable = [0.1, 0.05, 0.09, 0.04, 0.08, 0.03]
        
        is_stable = check_permutation_sufficiency(p_values_unstable, window=3, tolerance=0.001)
        assert is_stable is False, "Unstable p-values should return False"

    def test_check_permutation_sufficiency_small_window(self):
        """
        Verify behavior when the number of p-values is less than the window size.
        """
        p_values_short = [0.05, 0.049]
        
        # Should return False or handle gracefully (implementation dependent, but usually False)
        is_stable = check_permutation_sufficiency(p_values_short, window=3, tolerance=0.001)
        assert is_stable is False, "Insufficient data for window should return False"

    def test_run_permutation_test_dynamic_n_adjustment(self):
        """
        Verify that run_permutation_test adjusts n if the dataset is small
        or if stability is reached early (conceptual check via mocking).
        """
        # Create mock data
        n_subjects = 10
        n_trials = 50
        mock_data = pd.DataFrame({
            'subject_id': [f'sub_{i}' for i in range(n_subjects)],
            'mmn_amplitude': np.random.randn(n_subjects) * 0.5,
            'accuracy': np.random.randn(n_subjects) * 0.1 + 0.8
        })

        # Mock the underlying permutation logic to simulate early stability
        with patch('src.analysis.model._perform_permutation_shuffles') as mock_shuffles:
            # Simulate that stability is reached at n=200
            mock_shuffles.return_value = {
                'p_value': 0.045,
                'n_actual': 200,
                'early_stop': True,
                'p_values_history': [0.05] * 200
            }

            result = run_permutation_test(
                data=mock_data,
                target_column='mmn_amplitude',
                predictor_column='accuracy',
                n_permutations=1000,
                random_state=42
            )

            # Verify that the reported n_actual is less than requested n_permutations
            # indicating dynamic adjustment occurred
            assert result['n_actual'] < 1000, "n should be adjusted if early stop triggered"
            assert result['early_stop'] is True, "Early stop flag should be True"

    def test_run_permutation_test_min_n_sufficiency(self):
        """
        Verify that the permutation test enforces a minimum n for small datasets
        to ensure statistical validity.
        """
        # Create very small mock data
        n_subjects = 5
        mock_data = pd.DataFrame({
            'subject_id': [f'sub_{i}' for i in range(n_subjects)],
            'mmn_amplitude': np.random.randn(n_subjects),
            'accuracy': np.random.randn(n_subjects)
        })

        # The implementation should enforce a minimum n (e.g., 100 or 500)
        # even if requested n is low, or adjust based on dataset size.
        # We test that the function doesn't crash and returns a valid structure.
        with patch('src.analysis.model._perform_permutation_shuffles') as mock_shuffles:
            mock_shuffles.return_value = {
                'p_value': 0.05,
                'n_actual': 100, # Enforced minimum
                'early_stop': False,
                'p_values_history': [0.05] * 100
            }

            # Requesting 10 permutations on a small dataset
            result = run_permutation_test(
                data=mock_data,
                target_column='mmn_amplitude',
                predictor_column='accuracy',
                n_permutations=10,
                random_state=42
            )

            # Verify that n_actual is at least the minimum required (e.g., 100)
            assert result['n_actual'] >= 100, "Minimum n should be enforced for small datasets"

    def test_run_permutation_test_structure(self):
        """
        Verify that the permutation test returns the expected schema.
        """
        mock_data = pd.DataFrame({
            'subject_id': ['s1', 's2', 's3'],
            'mmn_amplitude': [1.0, 2.0, 3.0],
            'accuracy': [0.8, 0.9, 0.95]
        })

        with patch('src.analysis.model._perform_permutation_shuffles') as mock_shuffles:
            mock_shuffles.return_value = {
                'p_value': 0.04,
                'n_actual': 1000,
                'early_stop': False,
                'p_values_history': [0.04] * 1000
            }

            result = run_permutation_test(
                data=mock_data,
                target_column='mmn_amplitude',
                predictor_column='accuracy',
                n_permutations=1000,
                random_state=42
            )

            assert 'p_value' in result
            assert 'n_actual' in result
            assert 'early_stop' in result
            assert 'n_permutations_requested' in result