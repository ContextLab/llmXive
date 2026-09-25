"""
Unit tests for scoring logic defined in config/scales.yaml.

This module verifies that the scoring algorithms in `code/analysis/scales.py`
correctly implement the weights and logic defined in `code/config/scales.yaml`.
"""
import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
import yaml
import pandas as pd
import numpy as np

# Add the project root to the path so we can import code modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analysis.scales import (
    load_scale_config,
    score_cesd,
    score_gad7,
    score_pcl5,
    apply_scale_scoring
)

class TestScaleScoring(unittest.TestCase):
    """Tests for CES-D, GAD-7, and PCL-5 scoring logic."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for test configs
        self.test_dir = tempfile.mkdtemp()
        
        # Define the path to the actual config file
        self.config_path = project_root / "code" / "config" / "scales.yaml"
        
        # Verify the config file exists
        if not self.config_path.exists():
            self.fail(f"Config file not found at {self.config_path}")

    def tearDown(self):
        """Clean up temporary files."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_load_scale_config(self):
        """Test that the scale configuration loads correctly."""
        config = load_scale_config(self.config_path)
        
        self.assertIn("CES-D", config)
        self.assertIn("GAD-7", config)
        self.assertIn("PCL-5", config)
        
        # Check expected keys
        self.assertEqual(config["CES-D"]["variable"], "depression")
        self.assertEqual(config["CES-D"]["type"], "aggregate_score")
        
        self.assertEqual(config["GAD-7"]["variable"], "anxiety")
        self.assertEqual(config["GAD-7"]["type"], "aggregate_score")
        
        self.assertEqual(config["PCL-5"]["variable"], "ptsd")
        self.assertEqual(config["PCL-5"]["type"], "aggregate_score")

    def test_score_cesd_simple(self):
        """Test CES-D scoring with simple known values."""
        # Create a mock dataframe with CES-D items (simplified for testing)
        # CES-D typically has 20 items, but we test with a subset for simplicity
        data = {
            'cesd_1': [1, 2, 3],
            'cesd_2': [0, 1, 2],
            'cesd_3': [1, 1, 1],
            'cesd_4': [2, 3, 4],
            # ... add more items to simulate a real scenario
        }
        # Add remaining items to make it a valid CES-D subset (20 items)
        for i in range(5, 21):
            data[f'cesd_{i}'] = [1] * 3
            
        df = pd.DataFrame(data)
        
        # Score the CES-D
        scores = score_cesd(df)
        
        self.assertEqual(len(scores), 3)
        self.assertTrue(all(s >= 0 for s in scores))
        self.assertTrue(all(s <= 60 for s in scores))  # Max score for 20 items * 3

    def test_score_gad7_simple(self):
        """Test GAD-7 scoring with simple known values."""
        # GAD-7 has 7 items
        data = {
            'gad_1': [0, 1, 2],
            'gad_2': [1, 2, 3],
            'gad_3': [0, 1, 1],
            'gad_4': [1, 2, 2],
            'gad_5': [0, 1, 2],
            'gad_6': [1, 1, 1],
            'gad_7': [0, 1, 2],
        }
        df = pd.DataFrame(data)
        
        scores = score_gad7(df)
        
        self.assertEqual(len(scores), 3)
        self.assertTrue(all(s >= 0 for s in scores))
        self.assertTrue(all(s <= 21 for s in scores))  # Max score 7 * 3

    def test_score_pcl5_simple(self):
        """Test PCL-5 scoring with simple known values."""
        # PCL-5 has 20 items
        data = {
            'pcl_1': [0, 1, 2],
            'pcl_2': [1, 2, 3],
            'pcl_3': [0, 1, 1],
            'pcl_4': [1, 2, 2],
            'pcl_5': [0, 1, 2],
            'pcl_6': [1, 1, 1],
            'pcl_7': [0, 1, 2],
            'pcl_8': [1, 2, 2],
            'pcl_9': [0, 1, 1],
            'pcl_10': [1, 2, 2],
            'pcl_11': [0, 1, 2],
            'pcl_12': [1, 1, 1],
            'pcl_13': [0, 1, 2],
            'pcl_14': [1, 2, 2],
            'pcl_15': [0, 1, 1],
            'pcl_16': [1, 2, 2],
            'pcl_17': [0, 1, 2],
            'pcl_18': [1, 1, 1],
            'pcl_19': [0, 1, 2],
            'pcl_20': [1, 2, 2],
        }
        df = pd.DataFrame(data)
        
        scores = score_pcl5(df)
        
        self.assertEqual(len(scores), 3)
        self.assertTrue(all(s >= 0 for s in scores))
        self.assertTrue(all(s <= 80 for s in scores))  # Max score 20 * 4

    def test_apply_scale_scoring(self):
        """Test the full apply_scale_scoring function."""
        # Create a comprehensive dataframe with all required items
        data = {}
        
        # CES-D items (20)
        for i in range(1, 21):
            data[f'cesd_{i}'] = [1] * 5
        
        # GAD-7 items (7)
        for i in range(1, 8):
            data[f'gad_{i}'] = [1] * 5
        
        # PCL-5 items (20)
        for i in range(1, 21):
            data[f'pcl_{i}'] = [1] * 5
        
        df = pd.DataFrame(data)
        
        # Apply scoring
        result_df = apply_scale_scoring(df, self.config_path)
        
        # Check that the new columns exist
        self.assertIn('depression', result_df.columns)
        self.assertIn('anxiety', result_df.columns)
        self.assertIn('ptsd', result_df.columns)
        
        # Check that the scores are reasonable
        self.assertEqual(len(result_df), 5)
        self.assertTrue(all(result_df['depression'] > 0))
        self.assertTrue(all(result_df['anxiety'] > 0))
        self.assertTrue(all(result_df['ptsd'] > 0))

    def test_missing_columns_handling(self):
        """Test that missing columns are handled gracefully."""
        # Create a dataframe with only some CES-D items
        data = {
            'cesd_1': [1, 2, 3],
            'cesd_2': [0, 1, 2],
            # Missing other items
        }
        df = pd.DataFrame(data)
        
        # This should raise an error or return NaNs depending on implementation
        # We test that it doesn't crash unexpectedly
        try:
            scores = score_cesd(df)
            # If it doesn't crash, check that we got the right length
            self.assertEqual(len(scores), 3)
        except ValueError as e:
            # Expected if the function requires all items
            self.assertIn("missing", str(e).lower())

    def test_config_variable_mapping(self):
        """Test that the config correctly maps variables to column names."""
        config = load_scale_config(self.config_path)
        
        # Verify the variable names match what the functions expect
        self.assertEqual(config["CES-D"]["variable"], "depression")
        self.assertEqual(config["GAD-7"]["variable"], "anxiety")
        self.assertEqual(config["PCL-5"]["variable"], "ptsd")

    def test_score_ranges(self):
        """Test that scores fall within expected ranges."""
        # Create a dataframe with minimum values
        min_data = {}
        for i in range(1, 21):
            min_data[f'cesd_{i}'] = [0] * 3
        for i in range(1, 8):
            min_data[f'gad_{i}'] = [0] * 3
        for i in range(1, 21):
            min_data[f'pcl_{i}'] = [0] * 3
        
        min_df = pd.DataFrame(min_data)
        min_scores = apply_scale_scoring(min_df, self.config_path)
        
        self.assertTrue(all(min_scores['depression'] == 0))
        self.assertTrue(all(min_scores['anxiety'] == 0))
        self.assertTrue(all(min_scores['ptsd'] == 0))
        
        # Create a dataframe with maximum values
        max_data = {}
        for i in range(1, 21):
            max_data[f'cesd_{i}'] = [3] * 3  # Assuming max is 3 for CES-D
        for i in range(1, 8):
            max_data[f'gad_{i}'] = [3] * 3  # Assuming max is 3 for GAD-7
        for i in range(1, 21):
            max_data[f'pcl_{i}'] = [4] * 3  # Assuming max is 4 for PCL-5
        
        max_df = pd.DataFrame(max_data)
        max_scores = apply_scale_scoring(max_df, self.config_path)
        
        # Check maximum possible scores
        self.assertTrue(all(max_scores['depression'] == 60))  # 20 * 3
        self.assertTrue(all(max_scores['anxiety'] == 21))     # 7 * 3
        self.assertTrue(all(max_scores['ptsd'] == 80))        # 20 * 4

if __name__ == '__main__':
    unittest.main()