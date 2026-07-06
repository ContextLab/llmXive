"""
Unit tests for metrics extraction logic in User Story 2.
Specifically tests sliding window correlation and Louvain clustering state transitions.
"""
import pytest
import numpy as np
import networkx as nx
from networkx.algorithms.community import louvain_communities
from typing import List, Tuple, Dict
import sys
import os

# Add parent directory to path to allow imports from code/
# In a real CI environment, this would be handled by PYTHONPATH or package installation
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from analysis.metrics import (
    calculate_sliding_window_correlation,
    calculate_louvain_partitions,
    count_state_transitions,
    calculate_flexibility
)


class TestSlidingWindowCorrelation:
    """Tests for T023: Unit test for sliding window correlation matrix generation."""

    def test_window_shape(self):
        """Verify output shape matches (num_windows, num_nodes, num_nodes)."""
        # Create synthetic time series: 10 nodes, 100 timepoints
        np.random.seed(42)
        ts = np.random.randn(10, 100)
        window_size = 30
        step_size = 10

        windows = calculate_sliding_window_correlation(ts, window_size, step_size)

        expected_windows = int((100 - window_size) / step_size) + 1
        assert windows.shape == (expected_windows, 10, 10), \
            f"Expected shape ({expected_windows}, 10, 10), got {windows.shape}"

    def test_symmetry(self):
        """Verify correlation matrices are symmetric."""
        np.random.seed(42)
        ts = np.random.randn(5, 50)
        windows = calculate_sliding_window_correlation(ts, window_size=20, step_size=10)

        for i, mat in enumerate(windows):
            np.testing.assert_array_almost_equal(mat, mat.T, decimal=5,
                                                 err_msg=f"Window {i} is not symmetric")

    def test_diagonal_ones(self):
        """Verify diagonal elements are 1.0 (self-correlation)."""
        np.random.seed(42)
        ts = np.random.randn(8, 60)
        windows = calculate_sliding_window_correlation(ts, window_size=25, step_size=5)

        for mat in windows:
            np.testing.assert_array_almost_equal(np.diag(mat), np.ones(mat.shape[0]),
                                                 decimal=5, err_msg="Diagonal is not all 1s")


class TestLouvainStateTransitions:
    """Tests for T024: Unit test for Louvain clustering state transition calculation."""

    def test_partition_generation(self):
        """Verify Louvain clustering produces valid partitions for each window."""
        # Create a correlation matrix with clear community structure
        # 2 communities of 5 nodes each
        n_nodes = 10
        corr_mat = np.eye(n_nodes)
        # High correlation within communities
        for i in range(5):
            for j in range(5):
                if i != j:
                    corr_mat[i, j] = 0.8
        # Low correlation between communities
        for i in range(5):
            for j in range(5, 10):
                corr_mat[i, j] = 0.1
                corr_mat[j, i] = 0.1

        partitions = calculate_louvain_partitions([corr_mat])
        assert len(partitions) == 1, "Should produce 1 partition for 1 window"

        # Check that nodes are assigned to communities
        partition = partitions[0]
        assert len(partition) == n_nodes, "Partition should have same number of nodes"
        # All assignments should be integers >= 0
        assert all(isinstance(p, int) and p >= 0 for p in partition), \
            "Partition assignments must be non-negative integers"

    def test_state_transition_counting(self):
        """Verify state transitions are counted correctly between consecutive windows."""
        # Create two distinct community structures
        # Window 1: [0,0,0,0,0, 1,1,1,1,1] (2 communities)
        partition1 = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        # Window 2: [0,0,0,0,0, 1,1,1,1,1] (Same as Window 1 -> 0 transitions)
        partition2_same = [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]
        # Window 3: [1,1,1,1,1, 0,0,0,0,0] (Swapped -> 10 transitions)
        partition3_swapped = [1, 1, 1, 1, 1, 0, 0, 0, 0, 0]

        transitions_same = count_state_transitions(partition1, partition2_same)
        transitions_swapped = count_state_transitions(partition1, partition3_swapped)

        assert transitions_same == 0, "Same partitions should have 0 transitions"
        assert transitions_swapped == 10, "Swapped partitions should have 10 transitions"

    def test_transition_sequence(self):
        """Verify sequence of transitions across multiple windows."""
        partitions = [
            [0, 0, 0, 1, 1, 1],  # Window 1
            [0, 0, 0, 1, 1, 1],  # Window 2 (same as 1)
            [1, 1, 1, 0, 0, 0],  # Window 3 (swapped from 2)
            [1, 1, 1, 0, 0, 0],  # Window 4 (same as 3)
            [0, 1, 0, 1, 0, 1]   # Window 5 (randomized)
        ]

        # Expected transitions: 0 (1->2), 6 (2->3), 0 (3->4), 6 (4->5)
        expected_transitions = [0, 6, 0, 6]

        calculated_transitions = []
        for i in range(len(partitions) - 1):
            trans = count_state_transitions(partitions[i], partitions[i+1])
            calculated_transitions.append(trans)

        assert calculated_transitions == expected_transitions, \
            f"Expected {expected_transitions}, got {calculated_transitions}"

    def test_flexibility_calculation(self):
        """Verify flexibility (transitions per unit time) is calculated correctly."""
        # 10 nodes, 5 windows, 4 transitions total
        partitions = [
            [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
            [0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
        ]
        window_size = 30
        step_size = 10

        flexibility = calculate_flexibility(partitions, window_size, step_size)

        # Total transitions: 0 + 10 + 0 + 10 = 20
        # Total time span: (5-1) * step_size = 40
        # Flexibility = 20 / 40 = 0.5
        expected_flexibility = 20 / 40.0

        assert np.isclose(flexibility, expected_flexibility), \
            f"Expected flexibility {expected_flexibility}, got {flexibility}"

    def test_flexibility_single_window(self):
        """Verify flexibility handles single window case (division by zero protection)."""
        partitions = [[0, 0, 1, 1]]
        window_size = 30
        step_size = 10

        flexibility = calculate_flexibility(partitions, window_size, step_size)

        # Single window means 0 transitions and 0 time span -> should return 0.0
        assert flexibility == 0.0, "Single window should yield 0.0 flexibility"

    def test_network_specific_flexibility(self):
        """Verify flexibility can be calculated for specific network ROIs."""
        # Create partitions where we track specific nodes
        # Nodes 0-2: Network A, Nodes 3-5: Network B
        partitions = [
            [0, 0, 0, 1, 1, 1],  # A=0, B=1
            [0, 0, 0, 1, 1, 1],  # No change
            [1, 1, 1, 0, 0, 0],  # A=1, B=0 (Both changed)
            [0, 0, 0, 1, 1, 1],  # A=0, B=1 (Both changed back)
        ]

        # Test for Network A (nodes 0,1,2)
        network_a_indices = [0, 1, 2]
        flexibility_a = calculate_flexibility(partitions, 30, 10, node_indices=network_a_indices)

        # Transitions for A: 0->0 (0), 0->1 (3), 1->0 (3) = 6 total
        # Time span: 3 * 10 = 30
        # Flexibility: 6 / 30 = 0.2
        expected_a = 6 / 30.0

        assert np.isclose(flexibility_a, expected_a), \
            f"Network A flexibility: expected {expected_a}, got {flexibility_a}"


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_partitions(self):
        """Handle empty partition list gracefully."""
        with pytest.raises(ValueError, match="At least two partitions required"):
            count_state_transitions([], [])

    def test_mismatched_partition_sizes(self):
        """Detect mismatched partition sizes."""
        with pytest.raises(ValueError, match="Partition sizes must match"):
            count_state_transitions([0, 0, 1], [0, 0])

    def test_non_contiguous_communities(self):
        """Handle non-contiguous community assignments (e.g., 0, 2, 5)."""
        partition1 = [0, 2, 5, 0, 2, 5]
        partition2 = [0, 2, 5, 0, 2, 5]  # Same
        transitions = count_state_transitions(partition1, partition2)
        assert transitions == 0, "Identical non-contiguous assignments should have 0 transitions"

        partition3 = [5, 0, 2, 5, 0, 2]  # Shifted
        transitions_shifted = count_state_transitions(partition1, partition3)
        # All 6 nodes changed community
        assert transitions_shifted == 6, "Shifted assignments should have 6 transitions"