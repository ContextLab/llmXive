import unittest
import tempfile
import json
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.models.metrics.proportions import (
    load_topic_distributions,
    compute_topic_proportions,
    validate_proportion_vector,
    compute_all_window_proportions,
    save_topic_vectors,
    WINDOWS,
    K_TOPICS
)


class TestProportionsLogic(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_dir = Path(self.temp_dir.name)
        
        # Create sample topic distribution data for each window
        self.sample_data = {}
        for window in WINDOWS:
            # Create 100 documents with random topic distributions
            num_docs = 100
            doc_dists = np.random.dirichlet(np.ones(K_TOPICS), size=num_docs)
            self.sample_data[window] = doc_dists.tolist()
            
            # Save to file
            file_path = self.input_dir / f"topic_distributions_{window}.json"
            with open(file_path, 'w') as f:
                json.dump({"topics": doc_dists.tolist()}, f)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_load_topic_distributions(self):
        """Test loading topic distributions from JSON files."""
        distributions = load_topic_distributions(self.input_dir)
        
        self.assertEqual(len(distributions), len(WINDOWS))
        
        for window in WINDOWS:
            self.assertIn(window, distributions)
            self.assertIsInstance(distributions[window], list)
            self.assertEqual(len(distributions[window]), 100)
            
            # Check each document has K_TOPICS values
            for doc_dist in distributions[window]:
                self.assertEqual(len(doc_dist), K_TOPICS)
    
    def test_load_topic_distributions_missing_file(self):
        """Test that missing files raise FileNotFoundError."""
        # Remove one file
        missing_file = self.input_dir / "topic_distributions_2000-2004.json"
        missing_file.unlink()
        
        with self.assertRaises(FileNotFoundError):
            load_topic_distributions(self.input_dir)
    
    def test_compute_topic_proportions(self):
        """Test computing aggregate topic proportions."""
        # Create sample data
        num_docs = 100
        doc_dists = np.random.dirichlet(np.ones(K_TOPICS), size=num_docs)
        
        proportions = compute_topic_proportions(doc_dists.tolist())
        
        # Check shape
        self.assertEqual(len(proportions), K_TOPICS)
        
        # Check sum is 1.0
        self.assertAlmostEqual(np.sum(proportions), 1.0, places=5)
        
        # Check no NaN
        self.assertFalse(np.any(np.isnan(proportions)))
        
        # Check all non-negative
        self.assertTrue(np.all(proportions >= 0))
    
    def test_compute_topic_proportions_empty(self):
        """Test that empty input raises ValueError."""
        with self.assertRaises(ValueError):
            compute_topic_proportions([])
    
    def test_compute_topic_proportions_wrong_k(self):
        """Test that wrong number of topics raises ValueError."""
        # Create data with wrong number of topics
        wrong_k = 5
        doc_dists = np.random.dirichlet(np.ones(wrong_k), size=10)
        
        with self.assertRaises(ValueError):
            compute_topic_proportions(doc_dists.tolist(), k=wrong_k)
    
    def test_validate_proportion_vector_valid(self):
        """Test validation of a valid proportion vector."""
        valid_vector = np.array([0.1] * K_TOPICS)
        
        self.assertTrue(validate_proportion_vector(valid_vector))
    
    def test_validate_proportion_vector_nan(self):
        """Test that vector with NaN fails validation."""
        invalid_vector = np.array([0.1] * (K_TOPICS - 1) + [np.nan])
        
        self.assertFalse(validate_proportion_vector(invalid_vector))
    
    def test_validate_proportion_vector_negative(self):
        """Test that vector with negative values fails validation."""
        invalid_vector = np.array([0.1] * (K_TOPICS - 1) + [-0.1])
        
        self.assertFalse(validate_proportion_vector(invalid_vector))
    
    def test_validate_proportion_vector_wrong_sum(self):
        """Test that vector with wrong sum fails validation."""
        invalid_vector = np.array([0.1] * K_TOPICS) * 2  # Sum = 2.0
        
        self.assertFalse(validate_proportion_vector(invalid_vector))
    
    def test_validate_proportion_vector_wrong_length(self):
        """Test that vector with wrong length fails validation."""
        invalid_vector = np.array([0.1] * (K_TOPICS + 1))
        
        self.assertFalse(validate_proportion_vector(invalid_vector))
    
    def test_compute_all_window_proportions(self):
        """Test computing proportions for all windows."""
        proportions = compute_all_window_proportions(self.input_dir)
        
        self.assertEqual(len(proportions), len(WINDOWS))
        
        for window in WINDOWS:
            self.assertIn(window, proportions)
            prop_vector = proportions[window]
            
            # Check shape
            self.assertEqual(len(prop_vector), K_TOPICS)
            
            # Check sum is 1.0
            self.assertAlmostEqual(np.sum(prop_vector), 1.0, places=5)
            
            # Check no NaN
            self.assertFalse(np.any(np.isnan(prop_vector)))
    
    def test_save_topic_vectors(self):
        """Test saving topic vectors to JSON file."""
        # Create sample proportions
        proportions = {
            window: np.random.dirichlet(np.ones(K_TOPICS))
            for window in WINDOWS
        }
        
        output_path = self.input_dir / "topic_vectors.json"
        saved_path = save_topic_vectors(proportions, output_path)
        
        self.assertTrue(saved_path.exists())
        
        # Load and verify
        with open(saved_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["k_topics"], K_TOPICS)
        self.assertEqual(len(data["windows"]), len(WINDOWS))
        self.assertIn("topic_vectors", data)
        
        for window in WINDOWS:
            self.assertIn(window, data["topic_vectors"])
            self.assertEqual(len(data["topic_vectors"][window]), K_TOPICS)
    
    def test_save_topic_vectors_creates_directory(self):
        """Test that save_topic_vectors creates output directory if needed."""
        proportions = {
            window: np.random.dirichlet(np.ones(K_TOPICS))
            for window in WINDOWS
        }
        
        # Use a nested path that doesn't exist
        output_path = self.input_dir / "nested" / "path" / "topic_vectors.json"
        saved_path = save_topic_vectors(proportions, output_path)
        
        self.assertTrue(saved_path.exists())