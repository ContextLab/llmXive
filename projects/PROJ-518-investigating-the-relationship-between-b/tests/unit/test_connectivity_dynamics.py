import numpy as np
import pytest
from typing import List

from analysis.dynamics import calculate_flexibility


class TestCalculateFlexibility:
    """Unit tests for the calculate_flexibility function (T016/T040)."""

    def test_returns_float(self):
        """Verify that calculate_flexibility returns a float."""
        # Community labels for 3 ROIs over 4 time windows
        community_labels: List[List[int]] = [
            [0, 1, 0],  # Window 1
            [0, 1, 1],  # Window 2
            [1, 1, 0],  # Window 3
            [1, 0, 0],  # Window 4
        ]

        result = calculate_flexibility(community_labels)

        assert isinstance(result, float)

    def test_all_same_community(self):
        """If a ROI never changes community, it contributes 0 changes."""
        # All ROIs stay in community 0
        community_labels: List[List[int]] = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        result = calculate_flexibility(community_labels)

        # No changes, so flexibility should be 0.0
        assert result == 0.0

    def test_complete_switch_every_window(self):
        """If a ROI switches community every window, max changes."""
        # 2 ROIs, 3 windows. Each switches every time.
        # ROI 0: 0 -> 1 -> 0 (2 changes)
        # ROI 1: 1 -> 0 -> 1 (2 changes)
        community_labels: List[List[int]] = [
            [0, 1],
            [1, 0],
            [0, 1],
        ]

        result = calculate_flexibility(community_labels)

        # Total changes = 4, number of transitions = 2 per ROI * 2 ROIs = 4
        # Flexibility = 4 / 4 = 1.0
        assert result == 1.0

    def test_mixed_changes(self):
        """Test with a mix of changing and stable ROIs."""
        # ROI 0: 0 -> 0 -> 1 (1 change)
        # ROI 1: 1 -> 1 -> 1 (0 changes)
        # ROI 2: 2 -> 3 -> 2 (2 changes)
        # Total changes = 3, total transitions = 2 per ROI * 3 ROIs = 6
        # Expected = 3 / 6 = 0.5
        community_labels: List[List[int]] = [
            [0, 1, 2],
            [0, 1, 3],
            [1, 1, 2],
        ]

        result = calculate_flexibility(community_labels)

        assert np.isclose(result, 0.5)

    def test_single_window_returns_zero(self):
        """With only one window, there are no transitions, so flexibility is 0."""
        community_labels: List[List[int]] = [
            [0, 1, 2],
        ]

        result = calculate_flexibility(community_labels)

        assert result == 0.0

    def test_empty_input(self):
        """Empty list should return 0.0 to avoid division by zero."""
        community_labels: List[List[int]] = []

        result = calculate_flexibility(community_labels)

        assert result == 0.0

    def test_robust_to_numpy_types(self):
        """Ensure function handles numpy arrays as input if passed."""
        community_labels = [
            np.array([0, 1]),
            np.array([1, 0]),
            np.array([0, 1]),
        ]

        result = calculate_flexibility(community_labels)

        assert isinstance(result, float)
        assert result == 1.0
