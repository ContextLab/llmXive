import unittest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.models.lda.aligner import TopicAligner, align_topics_across_windows

class TestTopicAligner(unittest.TestCase):

    def setUp(self):
        self.aligner = TopicAligner(similarity_threshold=0.8)
        self.vocab_size = 100
        self.k = 5

    def test_cosine_similarity_identical(self):
        vec = np.random.rand(self.vocab_size)
        vec = vec / np.linalg.norm(vec)
        sim = self.aligner.cosine_similarity(vec, vec)
        self.assertAlmostEqual(sim, 1.0, places=5)

    def test_cosine_similarity_orthogonal(self):
        vec1 = np.zeros(self.vocab_size)
        vec1[0] = 1.0
        vec2 = np.zeros(self.vocab_size)
        vec2[1] = 1.0
        sim = self.aligner.cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, 0.0, places=5)

    def test_cosine_similarity_opposite(self):
        vec1 = np.zeros(self.vocab_size)
        vec1[0] = 1.0
        vec2 = np.zeros(self.vocab_size)
        vec2[0] = -1.0
        sim = self.aligner.cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, -1.0, places=5)

    def test_build_similarity_matrix(self):
        # Create two windows with distinct vectors
        w1_vecs = [np.random.rand(self.vocab_size) for _ in range(self.k)]
        w2_vecs = [np.random.rand(self.vocab_size) for _ in range(self.k)]

        data = {"w1": w1_vecs, "w2": w2_vecs}
        result = self.aligner.build_similarity_matrix(data)

        self.assertEqual(result["window1"], "w1")
        self.assertEqual(result["window2"], "w2")
        self.assertEqual(result["similarity_matrix"].shape, (self.k, self.k))

    def test_align_two_windows_with_perfect_match(self):
        # Create perfect matches
        base_vecs = [np.random.rand(self.vocab_size) for _ in range(self.k)]
        # Normalize
        base_vecs = [v / np.linalg.norm(v) for v in base_vecs]

        # w2 is a permutation of w1, but we want to test mapping
        # Let's say w2[i] is identical to w1[i]
        w1 = base_vecs
        w2 = [v.copy() for v in base_vecs]

        sim_matrix = np.eye(self.k) # Perfect diagonal

        mapping, scores = self.aligner.align_two_windows(sim_matrix)

        # Should map i -> i
        for i in range(self.k):
            self.assertEqual(mapping[i], i)
            self.assertGreater(scores[i], 0.9)

    def test_align_sequence(self):
        # Simulate 3 windows
        windows = ["w1", "w2", "w3"]
        data = {}

        # w1
        v1 = [np.random.rand(self.vocab_size) for _ in range(self.k)]
        v1 = [x/np.linalg.norm(x) for x in v1]
        data["w1"] = v1

        # w2: same as w1
        data["w2"] = [x.copy() for x in v1]

        # w3: same as w1
        data["w3"] = [x.copy() for x in v1]

        result = self.aligner.align_sequence(data, windows)

        self.assertIn("alignments", result)
        self.assertIn("reordered_vectors", result)
        self.assertIn("w1", result["reordered_vectors"])
        self.assertIn("w2", result["reordered_vectors"])
        self.assertIn("w3", result["reordered_vectors"])

        # Check that w2 and w3 are reordered correctly (should be same as w1)
        # Since they are identical, the mapping should be identity
        for i in range(self.k):
            # Check if vectors are close
            np.testing.assert_array_almost_equal(
                result["reordered_vectors"]["w2"][i],
                result["reordered_vectors"]["w1"][i],
                decimal=5
            )


class TestAlignTopicsAcrossWindows(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.input_path = os.path.join(self.temp_dir, "topic_vectors.json")
        self.output_path = os.path.join(self.temp_dir, "aligned.json")

        # Create mock data
        mock_data = {
            "windows": {
                "2000-2004": {
                    "topic_vectors": [np.random.rand(10).tolist() for _ in range(5)],
                    "metadata": {}
                },
                "2005-2009": {
                    "topic_vectors": [np.random.rand(10).tolist() for _ in range(5)],
                    "metadata": {}
                }
            }
        }
        with open(self.input_path, 'w') as f:
            json.dump(mock_data, f)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch('src.models.lda.aligner.load_topic_vectors_from_proportions')
    def test_align_topics_across_windows_calls_logic(self, mock_load):
        mock_data = {
            "windows": {
                "2000-2004": {"topic_vectors": [np.random.rand(10).tolist() for _ in range(5)]},
                "2005-2009": {"topic_vectors": [np.random.rand(10).tolist() for _ in range(5)]}
            }
        }
        mock_load.return_value = mock_data

        result = align_topics_across_windows(
            self.input_path,
            self.output_path,
            window_order=["2000-2004", "2005-2009"]
        )

        self.assertIn("alignment_metadata", result)
        self.assertIn("windows", result)
        self.assertTrue(os.path.exists(self.output_path))