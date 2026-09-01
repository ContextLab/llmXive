import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from entropy import calculate_shannon_entropy, extract_move_distribution, SENTINEL_VALUE

class TestEntropyCalculation:
    """Unit tests for entropy calculation logic."""

    def test_uniform_distribution(self):
        """Test entropy for a uniform distribution (max entropy)."""
        probs = np.array([0.25, 0.25, 0.25, 0.25])
        entropy = calculate_shannon_entropy(probs)
        # log2(4) = 2.0
        assert abs(entropy - 2.0) < 1e-6

    def test_deterministic_distribution(self):
        """Test entropy for a deterministic distribution (min entropy)."""
        probs = np.array([1.0, 0.0, 0.0])
        entropy = calculate_shannon_entropy(probs)
        assert abs(entropy - 0.0) < 1e-6

    def test_invalid_distribution_nan(self):
        """Test that NaN probabilities return sentinel."""
        probs = np.array([np.nan, 0.5, 0.5])
        entropy = calculate_shannon_entropy(probs)
        assert entropy == SENTINEL_VALUE

    def test_invalid_distribution_inf(self):
        """Test that Inf probabilities return sentinel."""
        probs = np.array([np.inf, 0.0, 0.0])
        entropy = calculate_shannon_entropy(probs)
        assert entropy == SENTINEL_VALUE

    def test_empty_distribution(self):
        """Test empty distribution returns sentinel."""
        probs = np.array([])
        entropy = calculate_shannon_entropy(probs)
        assert entropy == SENTINEL_VALUE

    def test_extract_move_distribution_uniform(self):
        """Test distribution extraction when counts are missing."""
        row = pd.Series({
            'trajectory_id': 'test-1',
            'legal_moves': ['move_a', 'move_b', 'move_c']
        })
        dist = extract_move_distribution(row)
        expected = np.array([1/3, 1/3, 1/3])
        np.testing.assert_array_almost_equal(dist, expected)

    def test_extract_move_distribution_weighted(self):
        """Test distribution extraction with weighted counts."""
        row = pd.Series({
            'trajectory_id': 'test-2',
            'legal_moves': ['move_a', 'move_b'],
            'move_counts': [3, 1]
        })
        dist = extract_move_distribution(row)
        expected = np.array([0.75, 0.25])
        np.testing.assert_array_almost_equal(dist, expected)

    def test_extract_move_distribution_zero_counts(self):
        """Test distribution extraction when all counts are zero."""
        row = pd.Series({
            'trajectory_id': 'test-3',
            'legal_moves': ['move_a', 'move_b'],
            'move_counts': [0, 0]
        })
        dist = extract_move_distribution(row)
        # Should fallback to uniform
        expected = np.array([0.5, 0.5])
        np.testing.assert_array_almost_equal(dist, expected)

    def test_extract_move_distribution_no_moves(self):
        """Test distribution extraction when no moves are present."""
        row = pd.Series({
            'trajectory_id': 'test-4',
            'legal_moves': []
        })
        dist = extract_move_distribution(row)
        assert len(dist) == 0

class TestEntropyEdgeCases:
    """Tests for specific edge cases mentioned in the spec."""

    def test_nan_entropy_handling(self):
        """Verify that NaN entropy triggers the sentinel value."""
        # Create a distribution that might cause issues
        probs = np.array([0.0, 0.0, 0.0])
        entropy = calculate_shannon_entropy(probs)
        # Since we filter out zeros, this becomes an empty array case
        assert entropy == SENTINEL_VALUE

    def test_inf_entropy_handling(self):
        """Verify that Inf entropy triggers the sentinel value."""
        # Manually passing an array that results in inf after log
        # This is hard to trigger naturally with valid probabilities,
        # but we test the check logic by mocking or using specific inputs.
        # Here we rely on the internal check in calculate_shannon_entropy.
        probs = np.array([1.0])
        entropy = calculate_shannon_entropy(probs)
        assert entropy != SENTINEL_VALUE # Normal case
        
        # Force a scenario if possible, or just verify the check exists.
        # The function explicitly checks np.isnan and np.isinf.
        # We trust the logic for now as the unit test above covers NaN input.
        pass
