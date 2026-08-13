"""
Unit tests for topic alignment logic (cosine similarity).

This module tests the TopicAligner and align_topics_across_windows functions
from src.models.lda.aligner. It verifies that:
1. Cosine similarity is computed correctly between topic vectors.
2. The alignment algorithm correctly maps topic indices across windows.
3. Edge cases (identical topics, orthogonal topics, empty inputs) are handled.
"""

import unittest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the functions to be tested
from src.models.lda.aligner import TopicAligner, align_topics_across_windows


class TestTopicAligner(unittest.TestCase):
    """Tests for the TopicAligner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.k = 10
        self.vocab_size = 100
        np.random.seed(42)
        
        # Create mock topic-word distributions (k x vocab_size)
        # Each row is a topic, each column is a word probability
        self.topic_vectors_window1 = np.random.rand(self.k, self.vocab_size)
        self.topic_vectors_window1 = self.topic_vectors_window1 / self.topic_vectors_window1.sum(axis=1, keepdims=True)
        
        self.topic_vectors_window2 = np.random.rand(self.k, self.vocab_size)
        self.topic_vectors_window2 = self.topic_vectors_window2 / self.topic_vectors_window2.sum(axis=1, keepdims=True)

    def test_cosine_similarity_computation(self):
        """Test that cosine similarity is computed correctly."""
        aligner = TopicAligner()
        
        # Test identical vectors (similarity should be 1.0)
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        sim = aligner.cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim, 1.0, places=5)
        
        # Test orthogonal vectors (similarity should be 0.0)
        vec3 = np.array([1.0, 0.0, 0.0])
        vec4 = np.array([0.0, 1.0, 0.0])
        sim = aligner.cosine_similarity(vec3, vec4)
        self.assertAlmostEqual(sim, 0.0, places=5)
        
        # Test opposite vectors (similarity should be -1.0)
        vec5 = np.array([1.0, 0.0, 0.0])
        vec6 = np.array([-1.0, 0.0, 0.0])
        sim = aligner.cosine_similarity(vec5, vec6)
        self.assertAlmostEqual(sim, -1.0, places=5)

    def test_similarity_matrix_shape(self):
        """Test that similarity matrix has correct shape."""
        aligner = TopicAligner()
        sim_matrix = aligner.compute_similarity_matrix(
            self.topic_vectors_window1, 
            self.topic_vectors_window2
        )
        self.assertEqual(sim_matrix.shape, (self.k, self.k))

    def test_similarity_matrix_values(self):
        """Test that similarity matrix values are in [-1, 1]."""
        aligner = TopicAligner()
        sim_matrix = aligner.compute_similarity_matrix(
            self.topic_vectors_window1, 
            self.topic_vectors_window2
        )
        self.assertTrue(np.all(sim_matrix >= -1.0))
        self.assertTrue(np.all(sim_matrix <= 1.0))

    def test_align_topics_returns_mapping(self):
        """Test that align_topics returns a valid topic mapping."""
        aligner = TopicAligner()
        mapping = aligner.align_topics(
            self.topic_vectors_window1, 
            self.topic_vectors_window2
        )
        
        # Mapping should be a dict with k keys
        self.assertIsInstance(mapping, dict)
        self.assertEqual(len(mapping), self.k)
        
        # All values should be in range [0, k-1]
        for src_topic, tgt_topic in mapping.items():
            self.assertIn(src_topic, range(self.k))
            self.assertIn(tgt_topic, range(self.k))

    def test_align_topics_bijective(self):
        """Test that the alignment mapping is bijective (one-to-one)."""
        aligner = TopicAligner()
        mapping = aligner.align_topics(
            self.topic_vectors_window1, 
            self.topic_vectors_window2
        )
        
        # Check that all target indices are unique
        target_indices = list(mapping.values())
        self.assertEqual(len(target_indices), len(set(target_indices)))
        self.assertEqual(len(target_indices), self.k)

    def test_align_topics_with_identical_topics(self):
        """Test alignment when topics are identical across windows."""
        aligner = TopicAligner()
        
        # Create identical topic vectors
        identical_vectors = self.topic_vectors_window1.copy()
        
        mapping = aligner.align_topics(
            self.topic_vectors_window1, 
            identical_vectors
        )
        
        # With identical topics, we expect identity mapping (or close to it)
        # Note: Due to potential tie-breaking, we just check validity
        self.assertEqual(len(mapping), self.k)

    def test_align_topics_with_permuted_topics(self):
        """Test alignment when topics are permuted across windows."""
        aligner = TopicAligner()
        
        # Create permuted topic vectors
        perm_indices = np.random.permutation(self.k)
        permuted_vectors = self.topic_vectors_window1[perm_indices]
        
        mapping = aligner.align_topics(
            self.topic_vectors_window1, 
            permuted_vectors
        )
        
        # The mapping should correctly identify the permutation
        # i.e., mapping[i] should be the index where topic i moved to
        # Verify that applying the mapping recovers the original order
        recovered = np.zeros_like(permuted_vectors)
        for src_idx, tgt_idx in mapping.items():
            recovered[tgt_idx] = self.topic_vectors_window1[src_idx]
        
        # Check if recovered matches original (within floating point tolerance)
        self.assertTrue(np.allclose(recovered, self.topic_vectors_window1, atol=1e-6))

    def test_handle_empty_topics(self):
        """Test handling of empty topic vectors."""
        aligner = TopicAligner()
        
        # Create a topic vector with all zeros (should be handled gracefully)
        empty_topic = np.zeros(self.vocab_size)
        normal_topic = np.random.rand(self.vocab_size)
        normal_topic = normal_topic / normal_topic.sum()
        
        # This should not raise an exception
        sim = aligner.cosine_similarity(empty_topic, normal_topic)
        # Cosine similarity with zero vector is undefined, but we handle it
        # by returning 0.0 (or some defined value)
        self.assertIsInstance(sim, float)


class TestAlignTopicsAcrossWindows(unittest.TestCase):
    """Tests for the align_topics_across_windows function."""

    def setUp(self):
        """Set up test fixtures."""
        self.k = 10
        self.windows = ["2000-2004", "2005-2009", "2010-2014"]
        np.random.seed(42)
        
        # Create mock topic vectors for each window
        self.topic_vectors = {}
        for window in self.windows:
            vectors = np.random.rand(self.k, 100)
            vectors = vectors / vectors.sum(axis=1, keepdims=True)
            self.topic_vectors[window] = vectors

    def test_align_topics_across_windows_returns_dict(self):
        """Test that the function returns a dictionary of mappings."""
        alignments = align_topics_across_windows(self.topic_vectors, self.windows)
        
        self.assertIsInstance(alignments, dict)
        # Should have mappings for each window relative to the first
        self.assertEqual(len(alignments), len(self.windows) - 1)

    def test_align_topics_across_windows_structure(self):
        """Test the structure of returned alignments."""
        alignments = align_topics_across_windows(self.topic_vectors, self.windows)
        
        for i in range(1, len(self.windows)):
            window_key = f"{self.windows[0]}_to_{self.windows[i]}"
            self.assertIn(window_key, alignments)
            
            mapping = alignments[window_key]
            self.assertIsInstance(mapping, dict)
            self.assertEqual(len(mapping), self.k)
            
            # Check that all mappings are valid
            for src, tgt in mapping.items():
                self.assertIn(src, range(self.k))
                self.assertIn(tgt, range(self.k))

    def test_align_topics_across_windows_with_file_io(self):
        """Test alignment with actual file I/O (save/load)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            
            # Save topic vectors to files
            for window, vectors in self.topic_vectors.items():
                file_path = tmpdir_path / f"topics_{window.replace('-', '_')}.json"
                data = {
                    "window": window,
                    "k": self.k,
                    "vectors": vectors.tolist()
                }
                with open(file_path, 'w') as f:
                    json.dump(data, f)
            
            # Load and align
            loaded_vectors = {}
            for window in self.windows:
                file_path = tmpdir_path / f"topics_{window.replace('-', '_')}.json"
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    loaded_vectors[window] = np.array(data["vectors"])
            
            alignments = align_topics_across_windows(loaded_vectors, self.windows)
            
            self.assertIsInstance(alignments, dict)
            self.assertEqual(len(alignments), len(self.windows) - 1)

    def test_align_topics_across_windows_consistency(self):
        """Test that alignment is consistent when run multiple times."""
        alignments1 = align_topics_across_windows(self.topic_vectors, self.windows)
        alignments2 = align_topics_across_windows(self.topic_vectors, self.windows)
        
        # Alignments should be identical (deterministic)
        for key in alignments1:
            self.assertEqual(alignments1[key], alignments2[key])

    def test_align_topics_across_windows_with_two_windows(self):
        """Test alignment with exactly two windows."""
        two_windows = ["2000-2004", "2005-2009"]
        two_vectors = {w: self.topic_vectors[w] for w in two_windows}
        
        alignments = align_topics_across_windows(two_vectors, two_windows)
        
        self.assertEqual(len(alignments), 1)
        self.assertIn("2000-2004_to_2005-2009", alignments)
        self.assertEqual(len(alignments["2000-2004_to_2005-2009"]), self.k)

    def test_align_topics_across_windows_error_handling(self):
        """Test error handling for invalid inputs."""
        # Empty windows list
        with self.assertRaises(ValueError):
            align_topics_across_windows({}, [])
        
        # Mismatched number of windows
        with self.assertRaises(ValueError):
            align_topics_across_windows(self.topic_vectors, ["window1"])
        
        # Missing topic vectors for a window
        incomplete_vectors = {w: self.topic_vectors[w] for w in self.windows[:-1]}
        with self.assertRaises(ValueError):
            align_topics_across_windows(incomplete_vectors, self.windows)


if __name__ == '__main__':
    unittest.main()