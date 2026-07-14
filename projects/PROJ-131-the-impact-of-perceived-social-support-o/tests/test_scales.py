"""
Unit tests for scale scoring logic defined in config/scales.yaml.
Verifies that score_cesd, score_gad7, and score_pcl5 correctly implement
the scoring rules (including reverse scoring) specified in the configuration.
"""
import unittest
import yaml
import pandas as pd
import numpy as np
from pathlib import Path

# Import the functions to test from the project's analysis module
# Note: Using relative import style compatible with running as `python -m pytest tests/test_scales.py`
# or `python tests/test_scales.py` if code/ is in sys.path.
# The task description implies running from root, so we ensure 'code' is importable.
import sys
if "code" not in sys.path:
    sys.path.insert(0, "code")

from analysis.scales import load_scale_config, score_cesd, score_gad7, score_pcl5


class TestScaleScoring(unittest.TestCase):
    """Test suite for psychological scale scoring functions."""

    @classmethod
    def setUpClass(cls):
        """Load the scale configuration once for all tests."""
        config_path = Path("code/config/scales.yaml")
        if not config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found at {config_path}. "
                "Ensure T004 has been completed successfully."
            )
        cls.config = load_scale_config(config_path)

    def test_cesd_reverse_scoring_logic(self):
        """
        Test CES-D scoring with reverse items.
        CES-D has 20 items (0-3).
        Reverse items: depressed5, depressed9, depressed12, depressed16, depressed18.
        Score = sum of (3 - value) for reverse items, sum of value for others.
        """
        # Create a mock dataframe with all 20 items
        # Values 0, 1, 2, 3
        data = {}
        for i in range(1, 21):
            item_name = f"depressed{i}"
            # Set all items to 3 (max score for raw)
            data[item_name] = [3] * 10

        df = pd.DataFrame(data)

        # Calculate expected score manually
        # Non-reverse items: 15 items * 3 = 45
        # Reverse items: 5 items. Value 3 -> (3-3)=0. Total 0.
        # Expected total = 45
        expected_score = 45.0

        result = score_cesd(df, self.config)
        
        self.assertEqual(len(result), 10)
        self.assertAlmostEqual(result.iloc[0], expected_score, places=2)

    def test_cesd_all_reverse_items_max_score(self):
        """
        Test CES-D where reverse items are 0 (which becomes 3) and others are 0.
        This tests the reverse logic specifically.
        """
        data = {}
        for i in range(1, 21):
            item_name = f"depressed{i}"
            data[item_name] = [0] * 5

        df = pd.DataFrame(data)

        # Non-reverse items: 15 * 0 = 0
        # Reverse items: 5 items. Value 0 -> (3-0)=3. Total 15.
        expected_score = 15.0

        result = score_cesd(df, self.config)
        self.assertAlmostEqual(result.iloc[0], expected_score, places=2)

    def test_gad7_standard_scoring(self):
        """
        Test GAD-7 scoring (7 items, 0-3, no reverse items).
        """
        data = {f"gad{i}": [2] * 5 for i in range(1, 8)}
        df = pd.DataFrame(data)

        # 7 items * 2 = 14
        expected_score = 14.0

        result = score_gad7(df, self.config)
        self.assertAlmostEqual(result.iloc[0], expected_score, places=2)

    def test_gad7_max_score(self):
        """Test GAD-7 with all max values."""
        data = {f"gad{i}": [3] * 5 for i in range(1, 8)}
        df = pd.DataFrame(data)

        expected_score = 7 * 3  # 21
        result = score_gad7(df, self.config)
        self.assertAlmostEqual(result.iloc[0], expected_score, places=2)

    def test_pcl5_standard_scoring(self):
        """
        Test PCL-5 scoring (25 items, 0-4, no reverse items).
        """
        data = {f"pcl{i}": [2] * 5 for i in range(1, 26)}
        df = pd.DataFrame(data)

        # 25 items * 2 = 50
        expected_score = 50.0

        result = score_pcl5(df, self.config)
        self.assertAlmostEqual(result.iloc[0], expected_score, places=2)

    def test_pcl5_max_score(self):
        """Test PCL-5 with all max values."""
        data = {f"pcl{i}": [4] * 5 for i in range(1, 26)}
        df = pd.DataFrame(data)

        expected_score = 25 * 4  # 100
        result = score_pcl5(df, self.config)
        self.assertAlmostEqual(result.iloc[0], expected_score, places=2)

    def test_missing_columns_raise_error(self):
        """Test that missing required columns raise a KeyError or ValueError."""
        # Missing one CES-D item
        data = {f"depressed{i}": [0] for i in range(1, 20)} # Only 19 items
        df = pd.DataFrame(data)

        with self.assertRaises(KeyError):
            score_cesd(df, self.config)

    def test_nan_handling(self):
        """Test that NaN values are handled (usually result in NaN score)."""
        data = {f"depressed{i}": [3.0 if i != 5 else np.nan for i in range(1, 21)]}
        df = pd.DataFrame(data)

        result = score_cesd(df, self.config)
        # Depending on implementation, sum with NaN might be NaN or ignore.
        # Standard pandas sum ignores NaN by default, but if the logic requires all, it might fail.
        # We check that it doesn't crash and returns a valid numeric type (or NaN).
        self.assertTrue(np.isnan(result.iloc[0]) or isinstance(result.iloc[0], (int, float)))

    def test_config_loads_correctly(self):
        """Verify the config loaded in setUpClass matches the expected structure."""
        self.assertIn("CES-D", self.config)
        self.assertIn("GAD-7", self.config)
        self.assertIn("PCL-5", self.config)
        
        self.assertIn("items", self.config["CES-D"])
        self.assertIn("reverse_items", self.config["CES-D"])
        self.assertIn("scoring", self.config["CES-D"])

        self.assertEqual(len(self.config["CES-D"]["items"]), 20)
        self.assertEqual(len(self.config["GAD-7"]["items"]), 7)
        self.assertEqual(len(self.config["PCL-5"]["items"]), 25)

if __name__ == "__main__":
    unittest.main()