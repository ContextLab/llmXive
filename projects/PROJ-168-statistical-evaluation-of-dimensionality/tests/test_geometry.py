"""
tests/test_geometry.py

Unit tests for the geometry.py module.
These tests verify the computation of Trustworthiness and Continuity metrics.
"""

import os
import sys
import tempfile
import json
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'code'))

from geometry import (
    GeometryError,
    _compute_seed,
    compute_linearity_metric,
    compute_continuity_metric,
    compute_geometry_metrics,
    run_geometry_analysis
)

class TestGeometryMetrics(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a small synthetic dataset for testing metrics
        # High-dimensional space (100 samples, 50 features)
        np.random.seed(42)
        self.X_high_dim = np.random.rand(100, 50)
        
        # Embedding space (100 samples, 2 features)
        self.X_embedding = np.random.rand(100, 2)
        
        # A more structured embedding (linear projection of high dim for better scores)
        self.X_linear_embedding = self.X_high_dim[:, :2]
        
    def test_compute_seed(self):
        """Test deterministic seed generation."""
        seed1 = _compute_seed("GSE123")
        seed2 = _compute_seed("GSE123")
        seed3 = _compute_seed("GSE456")
        
        self.assertEqual(seed1, seed2)
        self.assertNotEqual(seed1, seed3)
        self.assertIsInstance(seed1, int)

    def test_compute_linearity_metric(self):
        """Test Trustworthiness computation."""
        score = compute_linearity_metric(self.X_high_dim, self.X_embedding, k=5)
        
        # Trustworthiness is between 0 and 1
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        
        # Linear embedding should have higher trustworthiness than random
        score_linear = compute_linearity_metric(self.X_high_dim, self.X_linear_embedding, k=5)
        self.assertGreater(score_linear, score)

    def test_compute_continuity_metric(self):
        """Test Continuity computation."""
        score = compute_continuity_metric(self.X_high_dim, self.X_embedding, k=5)
        
        # Continuity is between 0 and 1
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_mismatched_dimensions(self):
        """Test that mismatched sample counts raise an error."""
        X_wrong = np.random.rand(50, 10)
        Z = np.random.rand(100, 2)
        
        with self.assertRaises(ValueError):
            compute_linearity_metric(X_wrong, Z)
        
        with self.assertRaises(ValueError):
            compute_continuity_metric(X_wrong, Z)

    def test_k_greater_than_samples(self):
        """Test handling of k >= n_samples."""
        X = np.random.rand(10, 5)
        Z = np.random.rand(10, 2)
        
        # Should not raise an error, but adjust k internally
        score = compute_linearity_metric(X, Z, k=20)
        self.assertGreaterEqual(score, 0.0)

    @patch('geometry._load_high_dim_data')
    @patch('geometry._load_embedding')
    def test_compute_geometry_metrics(self, mock_load_emb, mock_load_high):
        """Test the full metrics computation pipeline with mocked data loading."""
        # Mock the high-dimensional data
        mock_load_high.return_value = (self.X_high_dim, "GSE123")
        
        # Mock the embeddings
        mock_load_emb.side_effect = [
            self.X_embedding, # pca
            self.X_embedding, # tsne
            self.X_embedding  # umap
        ]
        
        result = compute_geometry_metrics("GSE123", ["pca", "tsne", "umap"], k=5)
        
        self.assertEqual(result["accession"], "GSE123")
        self.assertIn("pca", result["metrics"])
        self.assertIn("tsne", result["metrics"])
        self.assertIn("umap", result["metrics"])
        self.assertIn("trustworthiness", result["metrics"]["pca"])
        self.assertIn("continuity", result["metrics"]["pca"])

    @patch('geometry._load_high_dim_data')
    @patch('geometry._load_embedding')
    def test_compute_geometry_metrics_error_handling(self, mock_load_emb, mock_load_high):
        """Test error handling when loading data fails."""
        mock_load_high.side_effect = FileNotFoundError("Data not found")
        
        result = compute_geometry_metrics("GSE999", ["pca"], k=5)
        
        self.assertIn("error", result)
        self.assertIn("Data not found", result["error"])


if __name__ == '__main__':
    unittest.main()