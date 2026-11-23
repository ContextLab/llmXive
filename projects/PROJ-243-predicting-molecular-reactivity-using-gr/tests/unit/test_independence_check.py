"""
Unit tests for independence check functionality.
"""
import os
import sys
import json
import tempfile
import shutil
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'code'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.logging_utils import setup_logging
from config import set_config

# Import the functions to test
from importlib import import_module
independence_module = import_module('04_independence_check')

class TestIndependenceCheck(unittest.TestCase):
    """Test cases for independence check logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.artifacts_dir = os.path.join(self.temp_dir, "artifacts")
        os.makedirs(self.artifacts_dir)
        
        # Configure paths for testing
        set_config({
            "paths": {
                "artifacts": self.artifacts_dir,
                "data_raw": os.path.join(self.temp_dir, "data", "raw"),
                "data_processed": os.path.join(self.temp_dir, "data", "processed"),
                "data_assets": os.path.join(self.temp_dir, "data", "assets")
            }
        })

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_extract_errors(self):
        """Test error extraction from predictions."""
        predictions = {
            "predictions": {
                "spectral_gnn": {
                    "predicted": [1.0, 2.0, 3.0],
                    "true": [1.1, 2.1, 3.1]
                },
                "hetero_gnn": {
                    "predicted": [1.2, 2.2, 3.2],
                    "true": [1.1, 2.1, 3.1]
                }
            }
        }
        
        errors = independence_module.extract_errors(predictions)
        
        self.assertIn("spectral_gnn", errors)
        self.assertIn("hetero_gnn", errors)
        self.assertEqual(len(errors["spectral_gnn"]), 3)
        self.assertEqual(len(errors["hetero_gnn"]), 3)
        
        # Check error values
        np.testing.assert_array_almost_equal(errors["spectral_gnn"], [-0.1, -0.1, -0.1])
        np.testing.assert_array_almost_equal(errors["hetero_gnn"], [0.1, 0.1, 0.1])

    def test_extract_errors_missing_key(self):
        """Test error extraction with missing predictions key."""
        predictions = {"data": {}}
        
        with self.assertRaises(ValueError):
            independence_module.extract_errors(predictions)

    def test_tanimoto_similarity(self):
        """Test Tanimoto similarity calculation."""
        vec1 = np.array([1.0, 2.0, 3.0])
        vec2 = np.array([1.0, 2.0, 3.0])
        
        # Identical vectors should have Tanimoto = 1.0 (if non-zero)
        tanimoto = independence_module.tanimoto_similarity(vec1, vec2)
        self.assertGreater(tanimoto, 0.9)  # Allow for floating point precision
        
        # Orthogonal vectors
        vec3 = np.array([1.0, 0.0, 0.0])
        vec4 = np.array([0.0, 1.0, 0.0])
        tanimoto_orthogonal = independence_module.tanimoto_similarity(vec3, vec4)
        self.assertEqual(tanimoto_orthogonal, 0.0)

    def test_pearson_correlation(self):
        """Test Pearson correlation calculation."""
        vec1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        vec2 = np.array([2.0, 4.0, 6.0, 8.0, 10.0])  # Perfectly correlated
        
        corr, p_val = independence_module.pearson_correlation(vec1, vec2)
        self.assertAlmostEqual(corr, 1.0, places=5)
        self.assertLess(p_val, 0.01)

    def test_check_independence_correlated(self):
        """Test independence check with correlated errors."""
        # Create correlated errors
        base_error = np.random.randn(100)
        errors = {
            "model_a": base_error,
            "model_b": base_error + np.random.randn(100) * 0.1  # Highly correlated
        }
        
        results = independence_module.check_independence(errors)
        
        self.assertIn("correlation_coefficient", results)
        self.assertIn("p_value", results)
        self.assertIn("recommended_test", results)
        self.assertIn("is_correlated", results)
        
        # With high correlation, we expect p < 0.05
        if results["p_value"] < 0.05:
            self.assertTrue(results["is_correlated"])
            self.assertEqual(results["recommended_test"], "wilcoxon")
        else:
            self.assertFalse(results["is_correlated"])
            self.assertEqual(results["recommended_test"], "t-test")

    def test_check_independence_independent(self):
        """Test independence check with independent errors."""
        errors = {
            "model_a": np.random.randn(100),
            "model_b": np.random.randn(100)
        }
        
        results = independence_module.check_independence(errors)
        
        self.assertIn("pairwise_results", results)
        self.assertEqual(len(results["pairwise_results"]), 1)

    def test_save_results(self):
        """Test saving results to file."""
        results = {
            "correlation_coefficient": 0.5,
            "p_value": 0.03,
            "recommended_test": "wilcoxon",
            "is_correlated": True
        }
        
        output_path = os.path.join(self.artifacts_dir, "test_results.json")
        independence_module.save_results(results, output_path)
        
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded["correlation_coefficient"], 0.5)
        self.assertEqual(loaded["recommended_test"], "wilcoxon")

    def test_load_predictions_file_not_found(self):
        """Test loading predictions from non-existent file."""
        with self.assertRaises(FileNotFoundError):
            independence_module.load_predictions("/nonexistent/path.json")

    def test_main_integration(self):
        """Test the main function integration."""
        # Create a valid predictions file
        predictions = {
            "predictions": {
                "spectral_gnn": {
                    "predicted": [1.0, 2.0, 3.0, 4.0, 5.0],
                    "true": [1.1, 2.0, 3.2, 3.9, 5.1]
                },
                "hetero_gnn": {
                    "predicted": [1.2, 2.1, 3.1, 4.0, 5.0],
                    "true": [1.1, 2.0, 3.2, 3.9, 5.1]
                },
                "random_forest": {
                    "predicted": [0.9, 1.9, 3.3, 4.1, 4.9],
                    "true": [1.1, 2.0, 3.2, 3.9, 5.1]
                }
            }
        }
        
        predictions_path = os.path.join(self.artifacts_dir, "predictions.json")
        with open(predictions_path, 'w') as f:
            json.dump(predictions, f)
        
        # Run main
        independence_module.main()
        
        # Check output
        output_path = os.path.join(self.artifacts_dir, "independence_check_results.json")
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        self.assertIn("correlation_coefficient", results)
        self.assertIn("recommended_test", results)

if __name__ == "__main__":
    unittest.main()