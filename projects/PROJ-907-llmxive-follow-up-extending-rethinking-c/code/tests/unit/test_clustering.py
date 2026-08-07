import json
import numpy as np
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from src.clustering import (
    load_routing_cache,
    compute_mean_routing_vectors,
    perform_clustering,
    generate_global_average,
    save_null_hypothesis_flag,
    run_clustering_analysis
)
from src.config import get_results_path

class TestClusteringFallbackLogic:
    """Test the null hypothesis validation logic in clustering."""

    def test_save_null_hypothesis_flag_low_score(self, tmp_path):
        """Test that a flag file is created when score < 0.25."""
        output_path = tmp_path / "null_hypothesis_flag.json"
        
        # Low score should trigger null hypothesis
        is_null = save_null_hypothesis_flag(score=0.15, threshold=0.25, output_path=output_path)
        
        assert is_null is True
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["silhouette_score"] == 0.15
        assert data["is_null_hypothesis"] is True
        assert data["warning"] is not None
        assert "below threshold" in data["warning"].lower()

    def test_save_null_hypothesis_flag_high_score(self, tmp_path):
        """Test that no warning is generated when score >= 0.25."""
        output_path = tmp_path / "null_hypothesis_flag.json"
        
        # High score should NOT trigger null hypothesis
        is_null = save_null_hypothesis_flag(score=0.45, threshold=0.25, output_path=output_path)
        
        assert is_null is False
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["silhouette_score"] == 0.45
        assert data["is_null_hypothesis"] is False
        assert data["warning"] is None

    def test_run_clustering_analysis_triggers_null_flag(self, tmp_path):
        """Test that run_clustering_analysis creates the flag file when score is low."""
        # Create mock routing data that will result in low silhouette score
        # We'll mock perform_clustering to return a low score
        mock_centers = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_score = 0.1  # Low score
        mock_k = 2
        
        with patch('src.clustering.load_routing_cache') as mock_load, \
             patch('src.clustering.compute_mean_routing_vectors') as mock_mean, \
             patch('src.clustering.perform_clustering') as mock_cluster, \
             patch('src.clustering.get_results_path') as mock_get_path:
            
            # Setup mocks
            mock_load.return_value = [{"weights": np.random.rand(5, 10, 4)} for _ in range(3)]
            mock_mean.return_value = np.random.rand(10, 4)
            mock_cluster.return_value = (mock_centers, mock_score, mock_k)
            mock_get_path.return_value = tmp_path / "results"
            
            # Run analysis
            result = run_clustering_analysis()
            
            # Verify the flag file was created
            flag_path = tmp_path / "results" / "null_hypothesis_flag.json"
            assert flag_path.exists()
            
            with open(flag_path, 'r') as f:
                flag_data = json.load(f)
            
            assert flag_data["is_null_hypothesis"] is True
            assert result["is_null_hypothesis"] is True

    def test_save_null_hypothesis_flag_creates_directory(self, tmp_path):
        """Test that the function creates the output directory if it doesn't exist."""
        nested_path = tmp_path / "subdir" / "results" / "null_hypothesis_flag.json"
        
        save_null_hypothesis_flag(score=0.1, threshold=0.25, output_path=nested_path)
        
        assert nested_path.exists()

    def test_save_null_hypothesis_flag_default_path(self):
        """Test that the function uses the default results path when not specified."""
        with patch('src.clustering.get_results_path') as mock_get_path, \
             patch('pathlib.Path.exists') as mock_exists, \
             patch('pathlib.Path.mkdir') as mock_mkdir, \
             patch('builtins.open', MagicMock()) as mock_open:
            
            mock_get_path.return_value = Path("/default/results")
            mock_exists.return_value = True
            
            save_null_hypothesis_flag(score=0.1, threshold=0.25)
            
            # Verify the default path was used
            mock_get_path.assert_called_once()

    def test_edge_case_score_exactly_threshold(self, tmp_path):
        """Test behavior when score is exactly equal to the threshold."""
        output_path = tmp_path / "null_hypothesis_flag.json"
        
        # Score exactly at threshold should NOT be null hypothesis
        is_null = save_null_hypothesis_flag(score=0.25, threshold=0.25, output_path=output_path)
        
        assert is_null is False
        
        with open(output_path, 'r') as f:
            data = json.load(f)
        
        assert data["is_null_hypothesis"] is False