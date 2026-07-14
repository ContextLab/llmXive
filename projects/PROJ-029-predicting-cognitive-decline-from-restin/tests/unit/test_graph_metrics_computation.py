"""
Unit tests for graph metrics computation (T019).

Tests the individual functions in code/03_compute_graph_metrics.py
without requiring full dataset processing.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import tempfile
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code_03_compute_graph_metrics import (
    get_memory_usage_gb,
    check_memory_limit,
    process_single_subject_matrix,
    process_subject_wrapper
)
from utils.graph import create_graph_from_adjacency

class TestMemoryFunctions:
    """Test memory monitoring functions."""
    
    def test_get_memory_usage_gb(self):
        """Test that memory usage is returned as a positive float."""
        mem_gb = get_memory_usage_gb()
        assert isinstance(mem_gb, float)
        assert mem_gb > 0
        assert mem_gb < 100  # Sanity check: shouldn't be > 100GB
    
    def test_check_memory_limit(self):
        """Test memory limit checking logic."""
        # Current usage should be within limit
        current = get_memory_usage_gb()
        assert check_memory_limit(current, limit_gb=10.0) is True
        
        # Should return False if usage exceeds limit
        assert check_memory_limit(9.0, limit_gb=8.0) is False
        assert check_memory_limit(5.0, limit_gb=10.0) is True

class TestGraphMetrics:
    """Test graph metric computation functions."""
    
    @pytest.fixture
    def sample_matrix(self):
        """Create a sample 90x90 connectivity matrix."""
        np.random.seed(42)
        # Create a symmetric matrix with values between 0 and 1
        matrix = np.random.rand(90, 90)
        matrix = (matrix + matrix.T) / 2  # Make symmetric
        np.fill_diagonal(matrix, 0)  # No self-loops
        return matrix
    
    @pytest.fixture
    def temp_matrix_dir(self, sample_matrix, tmp_path):
        """Create a temporary directory with a sample matrix file."""
        matrix_file = tmp_path / "sub-001_connectivity.npy"
        np.save(matrix_file, sample_matrix)
        return tmp_path
    
    def test_process_single_subject_matrix(self, temp_matrix_dir):
        """Test processing a single subject matrix."""
        matrix_path = temp_matrix_dir / "sub-001_connectivity.npy"
        result = process_single_subject_matrix(matrix_path, "sub-001")
        
        assert result is not None
        assert "subject_id" in result
        assert result["subject_id"] == "sub-001"
        assert "avg_degree" in result
        assert "global_efficiency" in result
        assert "avg_clustering_coefficient" in result
        assert "avg_path_length" in result
        
        # Check that values are reasonable
        assert 0 <= result["avg_degree"] <= 1
        assert 0 <= result["global_efficiency"] <= 1
        assert 0 <= result["avg_clustering_coefficient"] <= 1
        # Path length can be inf for disconnected graphs, but should be positive otherwise
        if result["avg_path_length"] is not None:
            assert result["avg_path_length"] > 0
    
    def test_process_single_subject_invalid_shape(self, tmp_path):
        """Test processing a matrix with invalid shape."""
        # Create a 10x10 matrix (should be 90x90)
        invalid_matrix = np.random.rand(10, 10)
        matrix_file = tmp_path / "sub-002_connectivity.npy"
        np.save(matrix_file, invalid_matrix)
        
        result = process_single_subject_matrix(matrix_file, "sub-002")
        assert result is None
    
    def test_process_single_subject_missing_file(self):
        """Test processing a non-existent file."""
        result = process_single_subject_matrix(Path("nonexistent.npy"), "sub-003")
        assert result is None

class TestGraphProperties:
    """Test that computed graph properties are mathematically sound."""
    
    def test_degree_centrality_range(self):
        """Test that degree centrality values are in [0, 1]."""
        np.random.seed(42)
        matrix = np.random.rand(90, 90)
        matrix = (matrix + matrix.T) / 2
        np.fill_diagonal(matrix, 0)
        
        G = create_graph_from_adjacency(matrix)
        degree_centrality = G.degree()
        
        for node, degree in degree_centrality:
            # Degree centrality should be normalized between 0 and 1
            assert 0 <= degree <= 1
    
    def test_clustering_coefficient_range(self):
        """Test that clustering coefficient values are in [0, 1]."""
        np.random.seed(42)
        matrix = np.random.rand(90, 90)
        matrix = (matrix + matrix.T) / 2
        np.fill_diagonal(matrix, 0)
        
        G = create_graph_from_adjacency(matrix)
        from utils.graph import calculate_clustering_coefficient
        clustering = calculate_clustering_coefficient(G)
        
        for node, coef in clustering.items():
            assert 0 <= coef <= 1