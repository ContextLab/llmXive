import unittest
import tempfile
import os
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.models.lda.saver import (
    load_topic_vectors_from_proportions,
    save_final_topic_vectors,
    update_manifest_with_analysis_params
)

class TestSaverLogic(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.processed_dir = Path(self.temp_dir.name) / "processed"
        self.processed_dir.mkdir()
        self.output_file = Path(self.temp_dir.name) / "topic_vectors.json"
        self.manifest_file = Path(self.temp_dir.name) / "manifest.json"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_load_topic_vectors_from_proportions(self):
        # Create mock input files
        window_1 = "2000-2004"
        window_2 = "2005-2009"
        vec_1 = np.array([0.1, 0.2, 0.3, 0.4])
        vec_2 = np.array([0.5, 0.5, 0.0, 0.0])

        # Write mock JSON files
        file_1 = self.processed_dir / "topic_proportions_2000_2004.json"
        file_2 = self.processed_dir / "topic_proportions_2005_2009.json"

        with open(file_1, 'w') as f:
            json.dump({"proportions": vec_1.tolist()}, f)
        with open(file_2, 'w') as f:
            json.dump({"proportions": vec_2.tolist()}, f)

        # Load
        result = load_topic_vectors_from_proportions(self.processed_dir)

        self.assertIn(window_1, result)
        self.assertIn(window_2, result)
        np.testing.assert_array_almost_equal(result[window_1], vec_1)
        np.testing.assert_array_almost_equal(result[window_2], vec_2)

    def test_load_topic_vectors_invalid_file(self):
        # Create a file without 'proportions' key
        bad_file = self.processed_dir / "topic_proportions_bad.json"
        with open(bad_file, 'w') as f:
            json.dump({"data": [1, 2, 3]}, f)

        result = load_topic_vectors_from_proportions(self.processed_dir)
        self.assertEqual(len(result), 0)

    def test_save_final_topic_vectors(self):
        vectors = {
            "2000-2004": np.array([0.1, 0.9]),
            "2005-2009": np.array([0.8, 0.2])
        }
        
        save_final_topic_vectors(vectors, self.output_file)

        self.assertTrue(self.output_file.exists())
        with open(self.output_file, 'r') as f:
            data = json.load(f)

        self.assertIn("vectors", data)
        self.assertIn("metadata", data)
        self.assertEqual(data["metadata"]["k_topics"], 2)
        self.assertEqual(data["metadata"]["coherence_threshold"], 0.4)
        self.assertEqual(data["vectors"]["2000-2004"], [0.1, 0.9])

    def test_update_manifest_with_analysis_params(self):
        # Create empty manifest
        with open(self.manifest_file, 'w') as f:
            json.dump({}, f)

        update_manifest_with_analysis_params(self.manifest_file, k_topics=10, coherence_threshold=0.45)

        with open(self.manifest_file, 'r') as f:
            manifest = json.load(f)

        self.assertEqual(manifest["analysis_params"]["k_topics"], 10)
        self.assertEqual(manifest["analysis_params"]["coherence_threshold"], 0.45)

    def test_update_manifest_creates_file_if_missing(self):
        missing_manifest = Path(self.temp_dir.name) / "missing_manifest.json"
        update_manifest_with_analysis_params(missing_manifest, k_topics=5, coherence_threshold=0.3)
        self.assertTrue(missing_manifest.exists())

if __name__ == '__main__':
    unittest.main()