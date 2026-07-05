"""
Unit tests for the TopicAligner module.
"""

import unittest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.models.lda.aligner import TopicAligner, align_topics_across_windows


class TestTopicAligner(unittest.TestCase):
    """Test cases for the TopicAligner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.stats_dir = Path(self.temp_dir.name) / "stats"
        self.stats_dir.mkdir()
        
        # Create mock topic matrices
        self.n_topics = 10
        self.n_words = 100
        
        # Reference window matrix
        self.ref_matrix = np.random.rand(self.n_topics, self.n_words)
        self.ref_matrix = self.ref_matrix / self.ref_matrix.sum(axis=1, keepdims=True)
        
        # Target window matrix (with some similarity to reference)
        self.target_matrix = np.random.rand(self.n_topics, self.n_words)
        # Add some structure to make alignment meaningful
        self.target_matrix[0] = self.ref_matrix[0] * 0.9 + np.random.rand(self.n_words) * 0.1
        self.target_matrix[1] = self.ref_matrix[1] * 0.9 + np.random.rand(self.n_words) * 0.1
        self.target_matrix = self.target_matrix / self.target_matrix.sum(axis=1, keepdims=True)
        
        # Create mock topic_vectors.json
        self.topic_vectors_data = {
            "2000-2004": {"topics": self.ref_matrix.tolist()},
            "2005-2009": {"topics": self.target_matrix.tolist()}
        }
        
        topic_vectors_path = self.stats_dir / "topic_vectors.json"
        with open(topic_vectors_path, 'w') as f:
            json.dump(self.topic_vectors_data, f)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_topic_vectors(self):
        """Test loading topic vectors from JSON file."""
        aligner = TopicAligner()
        topic_matrices = aligner.load_topic_vectors(
            self.stats_dir, 
            ["2000-2004", "2005-2009"]
        )
        
        self.assertIn("2000-2004", topic_matrices)
        self.assertIn("2005-2009", topic_matrices)
        self.assertEqual(topic_matrices["2000-2004"].shape, (self.n_topics, self.n_words))
        self.assertEqual(topic_matrices["2005-2009"].shape, (self.n_topics, self.n_words))

    def test_compute_similarity_matrix(self):
        """Test cosine similarity computation."""
        aligner = TopicAligner()
        similarity = aligner.compute_similarity_matrix(
            self.ref_matrix, 
            self.target_matrix
        )
        
        self.assertEqual(similarity.shape, (self.n_topics, self.n_topics))
        # All values should be between -1 and 1
        self.assertTrue(np.all(similarity >= -1.0))
        self.assertTrue(np.all(similarity <= 1.0))
        
        # Self-similarity should be 1.0
        self_ref_sim = aligner.compute_similarity_matrix(self.ref_matrix, self.ref_matrix)
        np.testing.assert_array_almost_equal(
            np.diag(self_ref_sim), 
            np.ones(self.n_topics), 
            decimal=5
        )

    def test_find_optimal_permutation(self):
        """Test Hungarian algorithm for optimal assignment."""
        aligner = TopicAligner()
        similarity = aligner.compute_similarity_matrix(
            self.ref_matrix, 
            self.target_matrix
        )
        
        permutation = aligner.find_optimal_permutation(similarity)
        
        # Permutation should have the same length as number of topics
        self.assertEqual(len(permutation), self.n_topics)
        
        # All indices should be unique (valid permutation)
        self.assertEqual(len(set(permutation)), self.n_topics)
        self.assertTrue(np.all(permutation >= 0))
        self.assertTrue(np.all(permutation < self.n_topics))

    def test_align_window(self):
        """Test aligning a single window."""
        aligner = TopicAligner(reference_window="2000-2004")
        
        alignment_map, similarity_matrix = aligner.align_window(
            "2000-2004", 
            "2005-2009", 
            self.ref_matrix, 
            self.target_matrix
        )
        
        self.assertIn("2000-2004", aligner.alignment_map)
        self.assertIn("2005-2009", aligner.alignment_map)
        self.assertEqual(len(alignment_map), self.n_topics)
        
        # Check that alignment map is valid
        for target_idx, ref_idx in alignment_map.items():
            self.assertTrue(0 <= target_idx < self.n_topics)
            self.assertTrue(0 <= ref_idx < self.n_topics)

    def test_apply_alignment(self):
        """Test applying alignment to a topic vector."""
        aligner = TopicAligner(reference_window="2000-2004")
        
        # First align the windows
        aligner.align_window(
            "2000-2004", 
            "2005-2009", 
            self.ref_matrix, 
            self.target_matrix
        )
        
        # Create a test topic proportion vector
        test_vector = np.random.rand(self.n_topics)
        test_vector = test_vector / test_vector.sum()
        
        # Apply alignment
        aligned_vector = aligner.apply_alignment("2005-2009", test_vector)
        
        # Check that the aligned vector has the same sum
        np.testing.assert_almost_equal(
            test_vector.sum(), 
            aligned_vector.sum(), 
            decimal=10
        )
        
        # Check that the aligned vector has the same length
        self.assertEqual(len(aligned_vector), self.n_topics)

    def test_save_alignment_results(self):
        """Test saving alignment results to JSON."""
        aligner = TopicAligner(reference_window="2000-2004")
        
        # Perform alignment
        aligner.align_window(
            "2000-2004", 
            "2005-2009", 
            self.ref_matrix, 
            self.target_matrix
        )
        
        output_path = self.stats_dir / "alignment_output.json"
        aligner.save_alignment_results(output_path)
        
        # Check that file was created
        self.assertTrue(output_path.exists())
        
        # Check that file contains valid JSON
        with open(output_path, 'r') as f:
            results = json.load(f)
        
        self.assertIn("reference_window", results)
        self.assertEqual(results["reference_window"], "2000-2004")
        self.assertIn("alignment_maps", results)
        self.assertIn("2005-2009", results["alignment_maps"])

    def test_align_all_windows(self):
        """Test aligning multiple windows at once."""
        # Create additional mock data
        self.topic_vectors_data["2010-2014"] = {
            "topics": np.random.rand(self.n_topics, self.n_words).tolist()
        }
        
        with open(self.stats_dir / "topic_vectors.json", 'w') as f:
            json.dump(self.topic_vectors_data, f)
        
        aligner = TopicAligner(reference_window="2000-2004")
        topic_matrices = aligner.load_topic_vectors(
            self.stats_dir, 
            ["2000-2004", "2005-2009", "2010-2014"]
        )
        
        alignment_maps = aligner.align_all_windows(
            topic_matrices, 
            ["2000-2004", "2005-2009", "2010-2014"]
        )
        
        self.assertIn("2000-2004", alignment_maps)
        self.assertIn("2005-2009", alignment_maps)
        self.assertIn("2010-2014", alignment_maps)
        
        # Reference window should map to itself
        for i in range(self.n_topics):
            self.assertEqual(alignment_maps["2000-2004"][i], i)


class TestAlignTopicsAcrossWindows(unittest.TestCase):
    """Integration tests for the align_topics_across_windows function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.stats_dir = Path(self.temp_dir.name) / "stats"
        self.output_dir = Path(self.temp_dir.name) / "output"
        self.stats_dir.mkdir()
        self.output_dir.mkdir()
        
        # Create mock topic vectors
        n_topics = 5
        n_words = 50
        
        topic_vectors_data = {
            "2000-2004": {"topics": np.random.rand(n_topics, n_words).tolist()},
            "2005-2009": {"topics": np.random.rand(n_topics, n_words).tolist()},
            "2010-2014": {"topics": np.random.rand(n_topics, n_words).tolist()}
        }
        
        # Normalize
        for window_data in topic_vectors_data.values():
            topics = np.array(window_data["topics"])
            topics = topics / topics.sum(axis=1, keepdims=True)
            window_data["topics"] = topics.tolist()
        
        with open(self.stats_dir / "topic_vectors.json", 'w') as f:
            json.dump(topic_vectors_data, f)

    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()

    def test_align_topics_across_windows(self):
        """Test the main alignment function."""
        aligner = align_topics_across_windows(
            stats_dir=self.stats_dir,
            output_dir=self.output_dir,
            windows=["2000-2004", "2005-2009", "2010-2014"],
            reference_window="2000-2004"
        )
        
        # Check that alignment was performed
        self.assertIn("2000-2004", aligner.alignment_map)
        self.assertIn("2005-2009", aligner.alignment_map)
        self.assertIn("2010-2014", aligner.alignment_map)
        
        # Check that output file was created
        output_file = self.output_dir / "topic_alignment.json"
        self.assertTrue(output_file.exists())

    def test_align_topics_with_missing_file(self):
        """Test error handling when topic_vectors.json is missing."""
        empty_dir = Path(self.temp_dir.name) / "empty_stats"
        empty_dir.mkdir()
        
        with self.assertRaises(FileNotFoundError):
            align_topics_across_windows(
                stats_dir=empty_dir,
                output_dir=self.output_dir,
                windows=["2000-2004"]
            )


if __name__ == "__main__":
    unittest.main()