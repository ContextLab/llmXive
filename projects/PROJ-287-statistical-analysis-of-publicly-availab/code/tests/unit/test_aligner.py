import unittest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.models.lda.aligner import TopicAligner, align_topics_across_windows


class TestTopicAligner(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create sample topic vectors for testing
        self.sample_topic_vectors = {
            "2000-2004": [
                {"distribution": [0.8, 0.1, 0.1]},
                {"distribution": [0.1, 0.8, 0.1]},
                {"distribution": [0.1, 0.1, 0.8]}
            ],
            "2005-2009": [
                {"distribution": [0.75, 0.15, 0.1]},
                {"distribution": [0.15, 0.75, 0.1]},
                {"distribution": [0.1, 0.15, 0.75]}
            ]
        }
        
        # Save to temp file
        self.topic_vectors_path = self.temp_path / "topic_vectors.json"
        with open(self.topic_vectors_path, 'w') as f:
            json.dump(self.sample_topic_vectors, f)
        
        self.aligner = TopicAligner(reference_window="2000-2004")
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_load_topic_matrix(self):
        """Test loading topic matrix from file."""
        matrix = self.aligner.load_topic_matrix(self.topic_vectors_path, "2000-2004")
        
        self.assertEqual(matrix.shape, (3, 3))
        self.assertIsInstance(matrix, np.ndarray)
        
        # Check that values are reasonable
        self.assertTrue(np.all(matrix >= 0) and np.all(matrix <= 1))
    
    def test_compute_cosine_similarity(self):
        """Test cosine similarity computation."""
        matrix1 = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0]
        ])
        matrix2 = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0]
        ])
        
        similarity = self.aligner.compute_cosine_similarity(matrix1, matrix2)
        
        # Shape should be (2, 2)
        self.assertEqual(similarity.shape, (2, 2))
        
        # Diagonal should be 1.0 (perfect match)
        self.assertAlmostEqual(similarity[0, 0], 1.0, places=5)
        self.assertAlmostEqual(similarity[1, 1], 0.0, places=5)  # Orthogonal
    
    def test_align_window_to_reference(self):
        """Test alignment of a single window to reference."""
        reference_matrix = np.array([
            [0.8, 0.1, 0.1],
            [0.1, 0.8, 0.1],
            [0.1, 0.1, 0.8]
        ])
        
        target_matrix = np.array([
            [0.75, 0.15, 0.1],
            [0.15, 0.75, 0.1],
            [0.1, 0.15, 0.75]
        ])
        
        alignment_map = self.aligner.align_window_to_reference(
            reference_matrix, target_matrix, "2005-2009"
        )
        
        # Should have 3 mappings
        self.assertEqual(len(alignment_map), 3)
        
        # Each target index should map to a valid reference index
        for target_idx, ref_idx in alignment_map.items():
            self.assertIn(target_idx, [0, 1, 2])
            self.assertIn(ref_idx, [0, 1, 2])
    
    def test_align_all_windows(self):
        """Test alignment of all windows."""
        windows = ["2000-2004", "2005-2009"]
        
        alignment_maps = self.aligner.align_all_windows(
            self.topic_vectors_path, windows
        )
        
        # Should have maps for both windows
        self.assertIn("2000-2004", alignment_maps)
        self.assertIn("2005-2009", alignment_maps)
        
        # Reference window should have identity mapping
        ref_map = alignment_maps["2000-2004"]
        self.assertEqual(ref_map, {0: 0, 1: 1, 2: 2})
    
    def test_apply_alignment(self):
        """Test applying alignment and saving results."""
        windows = ["2000-2004", "2005-2009"]
        output_path = self.temp_path / "aligned_topic_vectors.json"
        
        result_path = self.aligner.apply_alignment(
            self.topic_vectors_path, windows, output_path
        )
        
        # Check that output file was created
        self.assertTrue(result_path.exists())
        
        # Check that file contains valid JSON
        with open(result_path, 'r') as f:
            aligned_data = json.load(f)
        
        self.assertIn("2000-2004", aligned_data)
        self.assertIn("2005-2009", aligned_data)


class TestAlignTopicsAcrossWindows(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        
        # Create sample topic vectors
        self.sample_data = {
            "2000-2004": [
                {"distribution": [0.9, 0.05, 0.05]},
                {"distribution": [0.05, 0.9, 0.05]}
            ],
            "2005-2009": [
                {"distribution": [0.85, 0.1, 0.05]},
                {"distribution": [0.1, 0.85, 0.05]}
            ]
        }
        
        self.topic_vectors_path = self.temp_path / "topic_vectors.json"
        with open(self.topic_vectors_path, 'w') as f:
            json.dump(self.sample_data, f)
    
    def tearDown(self):
        """Clean up."""
        self.temp_dir.cleanup()
    
    def test_align_topics_across_windows_function(self):
        """Test the convenience function."""
        alignment_maps, output_path = align_topics_across_windows(
            self.topic_vectors_path,
            windows=["2000-2004", "2005-2009"],
            reference_window="2000-2004"
        )
        
        # Check output path exists
        self.assertTrue(output_path.exists())
        
        # Check alignment maps
        self.assertIn("2000-2004", alignment_maps)
        self.assertIn("2005-2009", alignment_maps)
    
    def test_align_topics_across_windows_auto_windows(self):
        """Test auto-detection of windows from file."""
        alignment_maps, output_path = align_topics_across_windows(
            self.topic_vectors_path,
            reference_window="2000-2004"
        )
        
        # Should infer windows from file
        self.assertIn("2000-2004", alignment_maps)
        self.assertIn("2005-2009", alignment_maps)
    
    def test_align_topics_across_windows_file_not_found(self):
        """Test error handling for missing file."""
        with self.assertRaises(FileNotFoundError):
            align_topics_across_windows(
                Path("/nonexistent/path/topic_vectors.json")
            )