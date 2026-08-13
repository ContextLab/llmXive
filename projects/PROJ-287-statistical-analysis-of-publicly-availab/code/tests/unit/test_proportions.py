import unittest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.models.metrics.proportions import (
    load_topic_distributions,
    compute_topic_proportions,
    validate_proportion_vector,
    compute_all_window_proportions,
    save_topic_vectors,
    WINDOWS
)

class TestProportionsLogic(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())
        self.stats_dir = self.temp_dir / "stats"
        self.stats_dir.mkdir()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_validate_proportion_vector_valid(self):
        vec = np.array([0.1, 0.2, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        is_valid, msg = validate_proportion_vector(vec, k=10)
        self.assertTrue(is_valid)
        self.assertEqual(msg, "Valid")

    def test_validate_proportion_vector_nan(self):
        vec = np.array([0.1, np.nan, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        is_valid, msg = validate_proportion_vector(vec, k=10)
        self.assertFalse(is_valid)
        self.assertIn("NaN", msg)

    def test_validate_proportion_vector_negative(self):
        vec = np.array([0.1, -0.2, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        is_valid, msg = validate_proportion_vector(vec, k=10)
        self.assertFalse(is_valid)
        self.assertIn("negative", msg)

    def test_validate_proportion_vector_wrong_length(self):
        vec = np.array([0.1, 0.2, 0.3])
        is_valid, msg = validate_proportion_vector(vec, k=10)
        self.assertFalse(is_valid)
        self.assertIn("length", msg)

    def test_validate_proportion_vector_sum_not_one(self):
        vec = np.array([0.1, 0.2, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5]) # Sum = 1.5
        is_valid, msg = validate_proportion_vector(vec, k=10)
        self.assertFalse(is_valid)
        self.assertIn("sum", msg)

    def test_compute_topic_proportions(self):
        # Create a small matrix of document-topic distributions
        # 3 documents, 4 topics (using k=4 for test)
        doc_dists = np.array([
            [0.5, 0.5, 0.0, 0.0],
            [0.0, 0.5, 0.5, 0.0],
            [0.0, 0.0, 0.5, 0.5]
        ])
        
        result = compute_topic_proportions(doc_dists, k=4)
        
        expected = np.array([1/6, 1/3, 1/3, 1/6]) # Mean of columns
        self.assertTrue(np.allclose(result, expected))
        self.assertAlmostEqual(np.sum(result), 1.0)

    def test_load_topic_distributions_json_list(self):
        # Create a mock file with just a list
        window = "2000-2004"
        file_path = self.stats_dir / f"{window}_proportions.json"
        data = [0.1, 0.2, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_topic_distributions(window, self.stats_dir)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(len(result), 10)
        self.assertTrue(np.allclose(result, data))

    def test_load_topic_distributions_json_dict(self):
        window = "2005-2009"
        file_path = self.stats_dir / f"{window}_proportions.json"
        data = {"proportions": [0.0, 0.1, 0.2, 0.3, 0.4, 0.0, 0.0, 0.0, 0.0, 0.0]}
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_topic_distributions(window, self.stats_dir)
        self.assertIsInstance(result, np.ndarray)
        self.assertEqual(len(result), 10)
        self.assertTrue(np.allclose(result, data["proportions"]))

    def test_save_topic_vectors(self):
        proportions = {
            "2000-2004": np.array([0.1] * 10),
            "2005-2009": np.array([0.2] * 10)
        }
        output_path = self.temp_dir / "output.json"
        
        save_topic_vectors(proportions, output_path)
        
        self.assertTrue(output_path.exists())
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data["k_topics"], 10)
        self.assertIn("2000-2004", saved_data["topic_vectors"])
        self.assertIn("2005-2009", saved_data["topic_vectors"])
        self.assertTrue(np.allclose(saved_data["topic_vectors"]["2000-2004"], [0.1] * 10))

    def test_compute_all_window_proportions(self):
        # Create mock files for all windows
        for window in WINDOWS:
            file_path = self.stats_dir / f"{window}_proportions.json"
            data = [0.1] * 10
            with open(file_path, 'w') as f:
                json.dump(data, f)
        
        result = compute_all_window_proportions(self.stats_dir, k=10)
        
        self.assertEqual(len(result), len(WINDOWS))
        for window in WINDOWS:
            self.assertIn(window, result)
            self.assertTrue(np.allclose(result[window], [0.1] * 10))
            is_valid, _ = validate_proportion_vector(result[window], k=10)
            self.assertTrue(is_valid)

    def test_compute_all_window_proportions_missing_window(self):
        # Create files for only some windows
        for i, window in enumerate(WINDOWS):
            if i < 3: # Only first 3
                file_path = self.stats_dir / f"{window}_proportions.json"
                data = [0.1] * 10
                with open(file_path, 'w') as f:
                    json.dump(data, f)
        
        result = compute_all_window_proportions(self.stats_dir, k=10)
        
        # Should only return the ones that exist
        self.assertEqual(len(result), 3)
        self.assertIn(WINDOWS[0], result)
        self.assertNotIn(WINDOWS[3], result)

if __name__ == '__main__':
    unittest.main()