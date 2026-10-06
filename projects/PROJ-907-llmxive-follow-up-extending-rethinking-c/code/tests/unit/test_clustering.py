import json
import numpy as np
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

class TestClusteringFallbackLogic:
    def test_global_average_fallback(self):
        """Test that global average is used when clustering fails."""
        # Mock the clustering function to return a result that triggers the fallback
        with patch('src.clustering.perform_clustering') as mock_clustering:
            mock_clustering.return_value = {
                "centers": [],
                "silhouette": 0.1  # Below threshold
            }
            
            # Import the function to test
            from src.clustering import compute_canonical_map
            
            # Create a mock routing tensor
            routing_tensor = np.random.rand(10, 100, 10, 128)
            
            # Call the function
            result = compute_canonical_map(routing_tensor, distance_threshold=0.5)
            
            # Assert that the result is the global average
            expected_global_avg = np.mean(routing_tensor, axis=1)  # Average over timesteps
            np.testing.assert_array_almost_equal(result, expected_global_avg)

    def test_silhouette_threshold(self):
        """Test that silhouette score is checked correctly."""
        with patch('src.clustering.perform_clustering') as mock_clustering:
            mock_clustering.return_value = {
                "centers": [[0.5] * 128],
                "silhouette": 0.3  # Above threshold
            }
            
            from src.clustering import compute_canonical_map
            
            routing_tensor = np.random.rand(10, 100, 10, 128)
            
            result = compute_canonical_map(routing_tensor, distance_threshold=0.5)
            
            # Assert that the result is the cluster center
            expected_center = np.array([[0.5] * 128])
            np.testing.assert_array_almost_equal(result, expected_center)
