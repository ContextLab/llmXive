"""
Tests for T014: Recovery Segment Tagging Logic.

These tests verify the logic in code/utils/state_diff.py without requiring
a full dataset download. They use mock trajectory data to ensure the
identification logic works correctly.
"""
import unittest
import sys
import os
import ast
import json

# Add code directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.state_diff import identify_recovery_segments, calculate_state_diff_embedding

class TestRecoverySegmentTagging(unittest.TestCase):
    
    def test_identify_recovery_segments_empty_trajectory(self):
        """Test that empty trajectory returns empty list."""
        result = identify_recovery_segments([])
        self.assertEqual(result, [])

    def test_identify_recovery_segments_single_step(self):
        """Test that single step trajectory returns empty list."""
        trajectory = [{"observation": "single step"}]
        result = identify_recovery_segments(trajectory)
        self.assertEqual(result, [])

    def test_identify_recovery_segments_constant_state(self):
        """Test that constant state (no change) returns empty list."""
        # Using identical observations should result in near-zero diff
        trajectory = [
            {"observation": "state A"},
            {"observation": "state A"},
            {"observation": "state A"}
        ]
        # Note: Embeddings might have tiny floating point differences,
        # but with a 5% threshold and uniform zero-change, it should be empty
        # or very few. We assert it's not the full list if diff is truly 0.
        result = identify_recovery_segments(trajectory)
        # If total magnitude is 0, it should return empty
        self.assertEqual(result, [])

    def test_identify_recovery_segments_high_change(self):
        """Test that a trajectory with a massive state change identifies that segment."""
        # Create a trajectory where the last step is drastically different
        trajectory = [
            {"observation": "start state"},
            {"observation": "middle state"},
            {"observation": "END STATE WITH DRAMATIC CHANGE AND DIFFERENT WORDS"}
        ]
        result = identify_recovery_segments(trajectory)
        # We expect at least the last step (index 2) to be identified
        # because the change from step 1 to 2 is large
        self.assertIn(2, result)

    def test_identify_recovery_segments_threshold_calculation(self):
        """Test the 5% threshold logic specifically."""
        # Create a trajectory with known diffs
        # We can't easily control exact embedding diffs, but we can test the function signature
        # and that it returns a list of integers.
        trajectory = [
            {"observation": "obs 1"},
            {"observation": "obs 2"},
            {"observation": "obs 3"},
            {"observation": "obs 4"}
        ]
        result = identify_recovery_segments(trajectory, threshold_ratio=0.05)
        self.assertIsInstance(result, list)
        for idx in result:
            self.assertIsInstance(idx, int)
            self.assertGreaterEqual(idx, 0)
            self.assertLess(idx, len(trajectory))

    def test_calculate_state_diff_embedding_shape(self):
        """Test that embedding returns a list of floats."""
        emb = calculate_state_diff_embedding("test observation")
        self.assertIsInstance(emb, list)
        self.assertGreater(len(emb), 0)
        for val in emb:
            self.assertIsInstance(val, float)

if __name__ == '__main__':
    unittest.main()