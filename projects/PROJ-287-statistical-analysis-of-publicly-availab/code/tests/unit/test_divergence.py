"""
Unit tests for divergence metrics calculation.
"""

import unittest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.models.metrics.divergence import (
    calculate_js_divergence,
    calculate_js_divergence_matrix,
    validate_topic_distribution,
    load_topic_vectors_from_file,
    save_divergence_results,
    compute_pairwise_divergences
)


class TestJSDivergence(unittest.TestCase):
    """Test cases for Jensen-Shannon divergence calculation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.logger = None
    
    def test_identical_distributions(self):
        """JS divergence between identical distributions should be 0."""
        dist = np.array([0.5, 0.3, 0.2])
        result = calculate_js_divergence(dist, dist)
        self.assertAlmostEqual(result, 0.0, places=10)
    
    def test_disjoint_distributions(self):
        """JS divergence for disjoint distributions should be maximal (1.0 for base 2)."""
        dist1 = np.array([1.0, 0.0, 0.0])
        dist2 = np.array([0.0, 1.0, 0.0])
        result = calculate_js_divergence(dist1, dist2)
        # JS divergence for disjoint distributions with base 2 should be 1.0
        self.assertAlmostEqual(result, 1.0, places=5)
    
    def test_uniform_distributions(self):
        """JS divergence between uniform distributions should be 0."""
        dist1 = np.array([0.333, 0.334, 0.333])
        dist2 = np.array([0.333, 0.334, 0.333])
        result = calculate_js_divergence(dist1, dist2)
        self.assertAlmostEqual(result, 0.0, places=5)
    
    def test_different_distributions(self):
        """JS divergence should be positive for different distributions."""
        dist1 = np.array([0.7, 0.2, 0.1])
        dist2 = np.array([0.1, 0.2, 0.7])
        result = calculate_js_divergence(dist1, dist2)
        self.assertGreater(result, 0.0)
        self.assertLessEqual(result, 1.0)
    
    def test_symmetry(self):
        """JS divergence should be symmetric: JS(P||Q) = JS(Q||P)."""
        dist1 = np.array([0.6, 0.3, 0.1])
        dist2 = np.array([0.2, 0.5, 0.3])
        result1 = calculate_js_divergence(dist1, dist2)
        result2 = calculate_js_divergence(dist2, dist1)
        self.assertAlmostEqual(result1, result2, places=10)
    
    def test_invalid_negative_values(self):
        """Should raise ValueError for negative values."""
        dist1 = np.array([-0.1, 0.6, 0.5])
        dist2 = np.array([0.3, 0.4, 0.3])
        with self.assertRaises(ValueError):
            calculate_js_divergence(dist1, dist2)
    
    def test_invalid_zero_sum(self):
        """Should raise ValueError for zero-sum distributions."""
        dist1 = np.array([0.0, 0.0, 0.0])
        dist2 = np.array([0.3, 0.4, 0.3])
        with self.assertRaises(ValueError):
            calculate_js_divergence(dist1, dist2)
    
    def test_invalid_different_lengths(self):
        """Should raise ValueError for distributions of different lengths."""
        dist1 = np.array([0.5, 0.5])
        dist2 = np.array([0.3, 0.4, 0.3])
        with self.assertRaises(ValueError):
            calculate_js_divergence(dist1, dist2)
    
    def test_list_input(self):
        """Should accept list inputs and convert to numpy arrays."""
        dist1 = [0.5, 0.3, 0.2]
        dist2 = [0.2, 0.3, 0.5]
        result = calculate_js_divergence(dist1, dist2)
        self.assertGreater(result, 0.0)
    
    def test_normalization(self):
        """Should normalize distributions that don't sum to exactly 1.0."""
        dist1 = np.array([0.5, 0.3, 0.2000001])  # Slightly off
        dist2 = np.array([0.2, 0.3, 0.5])
        # Should not raise an error due to slight normalization difference
        result = calculate_js_divergence(dist1, dist2)
        self.assertGreaterEqual(result, 0.0)

class TestDivergenceMatrix(unittest.TestCase):
    """Test cases for divergence matrix calculation."""
    
    def test_matrix_symmetry(self):
        """Divergence matrix should be symmetric."""
        distributions = {
            'window1': np.array([0.5, 0.3, 0.2]),
            'window2': np.array([0.2, 0.5, 0.3]),
            'window3': np.array([0.3, 0.3, 0.4])
        }
        
        div_dict, div_matrix, window_names = calculate_js_divergence_matrix(distributions)
        
        # Check matrix symmetry
        self.assertTrue(np.allclose(div_matrix, div_matrix.T))
        
        # Check diagonal is zero
        self.assertTrue(np.allclose(np.diag(div_matrix), 0.0))
    
    def test_matrix_values_range(self):
        """All matrix values should be in [0, 1] for base 2."""
        distributions = {
            'w1': np.array([0.7, 0.2, 0.1]),
            'w2': np.array([0.1, 0.2, 0.7]),
            'w3': np.array([0.33, 0.34, 0.33])
        }
        
        _, div_matrix, _ = calculate_js_divergence_matrix(distributions)
        
        self.assertTrue(np.all(div_matrix >= 0))
        self.assertTrue(np.all(div_matrix <= 1.0))
    
    def test_window_ordering(self):
        """Window names should be sorted."""
        distributions = {
            'window2': np.array([0.5, 0.5]),
            'window1': np.array([0.5, 0.5]),
            'window3': np.array([0.5, 0.5])
        }
        
        _, _, window_names = calculate_js_divergence_matrix(distributions)
        
        self.assertEqual(window_names, ['window1', 'window2', 'window3'])

class TestValidation(unittest.TestCase):
    """Test cases for distribution validation."""
    
    def test_valid_distribution(self):
        """Valid distribution should pass validation."""
        dist = np.array([0.5, 0.3, 0.2])
        self.assertTrue(validate_topic_distribution(dist, 'test_window'))
    
    def test_invalid_negative(self):
        """Distribution with negative values should fail."""
        dist = np.array([0.5, -0.1, 0.6])
        with self.assertRaises(ValueError):
            validate_topic_distribution(dist, 'test_window')
    
    def test_invalid_sum(self):
        """Distribution not summing to 1 should fail."""
        dist = np.array([0.5, 0.3, 0.3])  # Sums to 1.1
        with self.assertRaises(ValueError):
            validate_topic_distribution(dist, 'test_window')
    
    def test_invalid_ndim(self):
        """Multi-dimensional array should fail."""
        dist = np.array([[0.5, 0.5], [0.5, 0.5]])
        with self.assertRaises(ValueError):
            validate_topic_distribution(dist, 'test_window')

class TestFileIO(unittest.TestCase):
    """Test cases for file I/O operations."""
    
    def setUp(self):
        """Create temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_divergence_results(self):
        """Test saving and loading divergence results."""
        results = {
            'method': 'Jensen-Shannon divergence',
            'base': 2,
            'windows': ['w1', 'w2'],
            'divergence_matrix': {
                'w1': {'w1': 0.0, 'w2': 0.5},
                'w2': {'w1': 0.5, 'w2': 0.0}
            },
            'metadata': {'num_windows': 2}
        }
        
        output_path = Path(self.temp_dir) / 'test_results.json'
        save_divergence_results(results, output_path)
        
        # Verify file exists
        self.assertTrue(output_path.exists())
        
        # Load and verify content
        with open(output_path, 'r') as f:
            loaded = json.load(f)
        
        self.assertEqual(loaded['method'], results['method'])
        self.assertEqual(loaded['base'], results['base'])
    
    def test_load_topic_vectors_from_json(self):
        """Test loading topic vectors from JSON file."""
        topic_data = {
            'window_2000_2004': [0.5, 0.3, 0.2],
            'window_2005_2009': [0.2, 0.5, 0.3],
            'window_2010_2014': [0.3, 0.3, 0.4]
        }
        
        input_path = Path(self.temp_dir) / 'topic_vectors.json'
        with open(input_path, 'w') as f:
            json.dump(topic_data, f)
        
        loaded = load_topic_vectors_from_file(input_path)
        
        self.assertEqual(len(loaded), 3)
        self.assertIsInstance(loaded['window_2000_2004'], np.ndarray)
        self.assertAlmostEqual(loaded['window_2000_2004'].sum(), 1.0)
    
    def test_compute_pairwise_divergences(self):
        """Test full pairwise divergence computation pipeline."""
        # Create test topic vectors
        topic_data = {
            'window1': [0.6, 0.3, 0.1],
            'window2': [0.2, 0.5, 0.3],
            'window3': [0.3, 0.3, 0.4]
        }
        
        input_path = Path(self.temp_dir) / 'topic_vectors.json'
        output_path = Path(self.temp_dir) / 'divergence_results.json'
        
        with open(input_path, 'w') as f:
            json.dump(topic_data, f)
        
        results = compute_pairwise_divergences(
            topic_vectors_path=input_path,
            output_path=output_path
        )
        
        # Verify results structure
        self.assertIn('method', results)
        self.assertIn('divergence_matrix', results)
        self.assertIn('windows', results)
        self.assertEqual(len(results['windows']), 3)
        
        # Verify output file was created
        self.assertTrue(output_path.exists())

class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""
    
    def test_very_small_values(self):
        """Should handle very small probability values."""
        dist1 = np.array([1e-10, 1e-10, 1.0 - 2e-10])
        dist2 = np.array([0.33, 0.34, 0.33])
        # Should not raise an error
        result = calculate_js_divergence(dist1, dist2)
        self.assertGreaterEqual(result, 0.0)
    
    def test_single_topic(self):
        """Should handle single-topic distributions."""
        dist1 = np.array([1.0])
        dist2 = np.array([1.0])
        result = calculate_js_divergence(dist1, dist2)
        self.assertAlmostEqual(result, 0.0, places=10)
    
    def test_nonexistent_file(self):
        """Should raise FileNotFoundError for missing topic vectors file."""
        with self.assertRaises(FileNotFoundError):
            load_topic_vectors_from_file('/nonexistent/path/file.json')
    
    def test_malformed_json(self):
        """Should handle malformed JSON in topic vectors file."""
        temp_file = Path(self.temp_dir) / 'malformed.json'
        with open(temp_file, 'w') as f:
            f.write('{ invalid json }')
        
        with self.assertRaises(json.JSONDecodeError):
            load_topic_vectors_from_file(temp_file)

if __name__ == '__main__':
    unittest.main()