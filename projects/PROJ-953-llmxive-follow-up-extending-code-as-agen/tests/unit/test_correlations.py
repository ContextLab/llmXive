"""
Unit tests for T033: Correlation Calculation.
"""
import os
import sys
import json
import tempfile
import unittest
import pandas as pd
from pathlib import Path
import numpy as np

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.calculate_correlations import encode_target, calculate_correlations


class TestEncodeTarget(unittest.TestCase):
    def test_encode_pass(self):
        self.assertEqual(encode_target("Pass"), 0)
        self.assertEqual(encode_target("pass"), 0)
        self.assertEqual(encode_target("  PASS  "), 0)

    def test_encode_fail(self):
        self.assertEqual(encode_target("Fail"), 1)
        self.assertEqual(encode_target("fail"), 1)
        self.assertEqual(encode_target("Timeout"), 1)
        self.assertEqual(encode_target("Unparseable"), 1)
        self.assertEqual(encode_target("Unknown"), 1)  # Default to 1 for safety


class TestCalculateCorrelations(unittest.TestCase):
    def setUp(self):
        # Create a mock features dataframe
        data = {
            'task_id': ['t1', 't2', 't3', 't4', 't5'],
            'dependency_depth': [1.0, 2.0, 3.0, 4.0, 5.0],
            'cyclomatic_complexity': [2.0, 4.0, 6.0, 8.0, 10.0],
            'lines_of_code': [10.0, 20.0, 30.0, 40.0, 50.0],
            'dynamic_execution_outcome': ['Pass', 'Fail', 'Fail', 'Timeout', 'Pass']
        }
        self.df = pd.DataFrame(data)
        self.model_path = "/tmp/mock_model.pkl"
        self.threshold_path = "/tmp/mock_threshold.json"

    def test_correlation_calculation(self):
        # Create dummy files to satisfy existence checks
        Path(self.model_path).touch()
        Path(self.threshold_path).write_text('{}')
        
        try:
            result = calculate_correlations(self.df, self.model_path, self.threshold_path)
            self.assertIsInstance(result, dict)
            self.assertIn('dependency_depth', result)
            self.assertIn('cyclomatic_complexity', result)
            self.assertIn('lines_of_code', result)
            
            # Check that correlations are numeric (or None)
            for k, v in result.items():
                if v is not None:
                    self.assertIsInstance(v, float)
                    self.assertGreaterEqual(v, -1.0)
                    self.assertLessEqual(v, 1.0)
        finally:
            # Cleanup
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
            if os.path.exists(self.threshold_path):
                os.remove(self.threshold_path)

    def test_missing_feature(self):
        df_missing = self.df.drop(columns=['dependency_depth'])
        Path(self.model_path).touch()
        Path(self.threshold_path).write_text('{}')
        
        try:
            result = calculate_correlations(df_missing, self.model_path, self.threshold_path)
            self.assertNotIn('dependency_depth', result)
            self.assertIn('cyclomatic_complexity', result)
        finally:
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
            if os.path.exists(self.threshold_path):
                os.remove(self.threshold_path)

    def test_insufficient_data(self):
        df_single = self.df.iloc[:1]
        Path(self.model_path).touch()
        Path(self.threshold_path).write_text('{}')
        
        try:
            result = calculate_correlations(df_single, self.model_path, self.threshold_path)
            # Should return None for correlations with insufficient data
            for v in result.values():
                self.assertIsNone(v)
        finally:
            if os.path.exists(self.model_path):
                os.remove(self.model_path)
            if os.path.exists(self.threshold_path):
                os.remove(self.threshold_path)


if __name__ == '__main__':
    unittest.main()