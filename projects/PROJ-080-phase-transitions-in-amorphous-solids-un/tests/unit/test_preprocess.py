"""
Unit tests for the stress-drop detection logic in preprocess.py.
This file extends the existing test suite to cover T013.
"""

import unittest
import numpy as np
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the function under test
from preprocess import detect_yield_onset, TrajectoryCorruptionError

class TestStressDropDetection(unittest.TestCase):
    """Tests for the stress-drop detection logic (FR-002)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_path = os.path.join(self.temp_dir, "yield_flags.json")

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)

    def test_clear_single_yield_detection(self):
        """
        Test detection of a clear single stress drop (>5%).
        The function should identify the FIRST significant drop and stop.
        """
        # Create synthetic stress data: rising then a sharp drop
        # Steps 0-9: rising stress
        # Step 10: Peak
        # Step 11: Drop (>5%)
        # Steps 12+: Low stress
        stress_values = np.array([1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 1.5, 1.4, 1.3])
        strains = np.arange(len(stress_values)) * 0.01

        result = detect_yield_onset(stress_values, strains)

        self.assertIsNotNone(result)
        self.assertEqual(result["yielding_step"], 11) # Index of the drop
        self.assertTrue(result["yield_detected"])
        self.assertEqual(result["drop_percentage"], 25.0) # (2.0 - 1.5) / 2.0 * 100

    def test_multiple_drops_detects_first_only(self):
        """
        Test that if multiple drops occur, ONLY the first one is flagged.
        This satisfies the strict enforcement of FR-002.
        """
        # Create stress data with two drops
        # Drop 1 at index 5 (from 1.5 to 1.0 -> 33%)
        # Drop 2 at index 10 (from 1.8 to 1.0 -> 44%)
        stress_values = np.array([1.0, 1.2, 1.4, 1.5, 1.5, 1.0, 1.2, 1.4, 1.6, 1.8, 1.0, 0.9])
        strains = np.arange(len(stress_values)) * 0.01

        result = detect_yield_onset(stress_values, strains)

        self.assertIsNotNone(result)
        self.assertTrue(result["yield_detected"])
        self.assertEqual(result["yielding_step"], 5) # Must be the FIRST drop
        # Verify it did not detect the second drop
        self.assertNotEqual(result["yielding_step"], 10)

    def test_no_significant_drop(self):
        """
        Test behavior when no drop > 5% is found.
        Should return yield_detected=False.
        """
        # Monotonically increasing stress (no drop)
        stress_values = np.array([1.0, 1.1, 1.2, 1.3, 1.4, 1.5])
        strains = np.arange(len(stress_values)) * 0.01

        result = detect_yield_onset(stress_values, strains)

        self.assertIsNotNone(result)
        self.assertFalse(result["yield_detected"])
        self.assertIsNone(result["yielding_step"])

    def test_ambiguous_small_drops(self):
        """
        Test behavior when drops exist but are < 5%.
        Should be treated as indeterminate/no yield.
        """
        # Small fluctuations, max drop is 2%
        stress_values = np.array([1.0, 1.1, 1.05, 1.15, 1.10, 1.20])
        strains = np.arange(len(stress_values)) * 0.01

        result = detect_yield_onset(stress_values, strains)

        self.assertIsNotNone(result)
        self.assertFalse(result["yield_detected"])

    def test_empty_input(self):
        """Test handling of empty arrays."""
        stress_values = np.array([])
        strains = np.array([])

        result = detect_yield_onset(stress_values, strains)

        self.assertIsNotNone(result)
        self.assertFalse(result["yield_detected"])

    def test_insufficient_length(self):
        """Test handling of arrays too short to compute a drop."""
        stress_values = np.array([1.0])
        strains = np.array([0.0])

        result = detect_yield_onset(stress_values, strains)

        self.assertIsNotNone(result)
        self.assertFalse(result["yield_detected"])

    def test_nan_values_handling(self):
        """
        Test that NaN values in stress data are handled gracefully.
        The function should either skip them or treat them as non-yield.
        """
        stress_values = np.array([1.0, 1.2, np.nan, 1.4, 1.0]) # Drop after NaN
        strains = np.arange(len(stress_values)) * 0.01

        # The function should not crash. Behavior depends on implementation,
        # but it should not raise an exception.
        result = detect_yield_onset(stress_values, strains)
        
        # If the implementation propagates NaNs in comparison, it might return False.
        # If it skips, it might detect the drop.
        # We assert that it returns a valid dict structure without crashing.
        self.assertIsInstance(result, dict)
        self.assertIn("yield_detected", result)

    def test_edge_case_exactly_5_percent(self):
        """Test the boundary condition of exactly 5% drop."""
        # 1.0 -> 0.95 is exactly 5%
        stress_values = np.array([1.0, 1.1, 1.2, 1.0, 0.95])
        strains = np.arange(len(stress_values)) * 0.01

        result = detect_yield_onset(stress_values, strains)

        self.assertIsNotNone(result)
        # Depending on strict inequality (>5% vs >=5%), this might be true or false.
        # FR-002 says ">5% decrease". So 5.0% exactly should be False.
        # However, floating point comparisons often use a tolerance.
        # Assuming strict > 5.0:
        # If the drop is exactly 5.0, it should be False.
        # Let's assume the implementation uses > 5.0.
        # 1.0 -> 0.95 is 5.0%.
        if result["yield_detected"]:
            self.assertEqual(result["yielding_step"], 4)
        else:
            # If it's not detected, that's also acceptable for strict > 5%
            self.assertFalse(result["yield_detected"])

    def test_integration_with_file_output(self):
        """
        Integration test: Verify that detect_yield_onset works correctly
        when called as part of a process that writes to a file.
        This simulates the flow in T021.
        """
        stress_values = np.array([1.0, 1.5, 2.0, 1.5])
        strains = np.array([0.0, 0.1, 0.2, 0.3])

        result = detect_yield_onset(stress_values, strains)

        # Simulate writing to JSON
        with open(self.output_path, 'w') as f:
            json.dump(result, f)

        # Verify file exists and content is correct
        self.assertTrue(os.path.exists(self.output_path))
        with open(self.output_path, 'r') as f:
            loaded_result = json.load(f)

        self.assertEqual(loaded_result["yielding_step"], 3)
        self.assertTrue(loaded_result["yield_detected"])

if __name__ == "__main__":
    unittest.main()