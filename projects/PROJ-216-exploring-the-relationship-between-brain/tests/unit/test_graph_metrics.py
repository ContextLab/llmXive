import os
import sys
import json
import numpy as np
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_metrics import (
    compute_global_efficiency,
    compute_clustering_coefficient,
    compute_modularity_louvain,
    compute_modularity_with_resolution_sweep,
    compute_graph_metrics,
    generate_correlation_matrix
)

class TestGraphMetrics:
    """Unit tests for graph metrics calculation."""

    def test_generate_correlation_matrix_symmetry(self):
        """Test that the generated correlation matrix is symmetric."""
        np.random.seed(42)
        # Create a time series: 100 time points, 200 regions (nodes)
        time_series = np.random.rand(100, 200)
        
        # Generate correlation matrix
        corr_matrix = generate_correlation_matrix(time_series)
        
        # Assert symmetry
        assert np.allclose(corr_matrix, corr_matrix.T), "Correlation matrix is not symmetric"
        assert corr_matrix.shape == (200, 200), "Correlation matrix shape is incorrect"
        
        # Assert diagonal is 1 (self-correlation)
        assert np.allclose(np.diag(corr_matrix), 1.0), "Diagonal elements are not 1.0"

    def test_global_efficiency_range(self):
        """Test that global efficiency is within valid range (0-1)."""
        np.random.seed(42)
        n = 50
        # Create a random positive semi-definite matrix to simulate correlations
        A = np.random.rand(n, n)
        corr_matrix = np.dot(A, A.T)
        d = np.sqrt(np.diag(corr_matrix))
        corr_matrix = corr_matrix / np.outer(d, d)
        np.fill_diagonal(corr_matrix, 1.0)
        
        eff = compute_global_efficiency(corr_matrix)
        
        assert 0 <= eff <= 1, f"Global efficiency {eff} is out of range [0, 1]"

    def test_clustering_coefficient_range(self):
        """Test that clustering coefficient is within valid range (0-1)."""
        np.random.seed(42)
        n = 50
        A = np.random.rand(n, n)
        corr_matrix = np.dot(A, A.T)
        d = np.sqrt(np.diag(corr_matrix))
        corr_matrix = corr_matrix / np.outer(d, d)
        np.fill_diagonal(corr_matrix, 1.0)
        
        cc = compute_clustering_coefficient(corr_matrix)
        
        assert 0 <= cc <= 1, f"Clustering coefficient {cc} is out of range [0, 1]"

    def test_modularity_louvain_range(self):
        """Test that modularity is within valid range (-1 to 1, typically 0-0.7)."""
        np.random.seed(42)
        n = 50
        A = np.random.rand(n, n)
        corr_matrix = np.dot(A, A.T)
        d = np.sqrt(np.diag(corr_matrix))
        corr_matrix = corr_matrix / np.outer(d, d)
        np.fill_diagonal(corr_matrix, 1.0)
        
        # Note: This test assumes the 'community' package is installed.
        # If not, it will raise an ImportError which is expected behavior
        # for the environment check.
        try:
            mod = compute_modularity_louvain(corr_matrix)
            assert -1 <= mod <= 1, f"Modularity {mod} is out of range [-1, 1]"
        except ImportError:
            # Skip if community package is not installed, but log it
            pytest.skip("community package not installed for modularity test")

    def test_modularity_resolution_sweep(self):
        """Test that resolution sweep returns a valid modularity value."""
        np.random.seed(42)
        n = 50
        A = np.random.rand(n, n)
        corr_matrix = np.dot(A, A.T)
        d = np.sqrt(np.diag(corr_matrix))
        corr_matrix = corr_matrix / np.outer(d, d)
        np.fill_diagonal(corr_matrix, 1.0)
        
        try:
            mod = compute_modularity_with_resolution_sweep(corr_matrix)
            assert -1 <= mod <= 1, f"Modularity from sweep {mod} is out of range [-1, 1]"
        except ImportError:
            pytest.skip("community package not installed for modularity sweep test")

    def test_modularity_fallback_on_failure(self):
        """Test that resolution sweep fallback triggers when standard modularity fails."""
        np.random.seed(42)
        n = 50
        A = np.random.rand(n, n)
        corr_matrix = np.dot(A, A.T)
        d = np.sqrt(np.diag(corr_matrix))
        corr_matrix = corr_matrix / np.outer(d, d)
        np.fill_diagonal(corr_matrix, 1.0)
        
        # Mock the community.louvain_communities to raise an error on first call
        # to simulate convergence failure, forcing the sweep fallback
        import graph_metrics
        
        call_count = 0
        def failing_louvain(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("Simulated convergence failure")
            # Return a mock partition for subsequent calls (sweep)
            return {0: 0, 1: 0, 2: 1} # Dummy partition
        
        with patch.object(graph_metrics, 'community') as mock_community:
            mock_community.louvain_communities = failing_louvain
            mock_community.modularity = lambda *args, **kwargs: 0.5 # Mock modularity calculation
            
            try:
                mod = compute_modularity_with_resolution_sweep(corr_matrix)
                # If we get here, the fallback worked
                assert call_count > 1, "Fallback resolution sweep was not triggered"
                assert -1 <= mod <= 1, f"Modularity from fallback {mod} is out of range [-1, 1]"
            except RuntimeError as e:
                # If the fallback also fails (e.g. modularity calculation fails), 
                # we still verify the logic attempted the sweep
                if "Simulated convergence failure" in str(e):
                    pytest.fail("Fallback logic did not handle the initial failure correctly")
                else:
                    raise

    def test_compute_graph_metrics_mock(self):
        """Test full graph metrics computation on a mock subject."""
        # Create a mock subject entry
        mock_subject = {
            'id': 'mock_sub_001',
            'path': Path('data/processed/mock_subject_001.nii.gz'),
            'is_mock': True
        }
        
        # Mock the time series generation for the mock subject
        with patch('graph_metrics.load_time_series_from_nifti') as mock_load:
            mock_load.return_value = np.random.rand(100, 200)
            
            metrics = compute_graph_metrics(mock_subject)
            
            assert 'subject_id' in metrics
            assert 'global_efficiency' in metrics
            assert 'clustering_coefficient' in metrics
            assert 'modularity' in metrics
            
            assert 0 <= metrics['global_efficiency'] <= 1
            assert 0 <= metrics['clustering_coefficient'] <= 1
            assert -1 <= metrics['modularity'] <= 1

    def test_compute_graph_metrics_real_file_missing(self):
        """Test that compute_graph_metrics handles missing real files gracefully or fails loudly."""
        # Create a subject entry without is_mock flag but with non-existent path
        subject = {
            'id': 'missing_sub',
            'path': Path('data/processed/does_not_exist.nii.gz'),
            'is_mock': False
        }
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            compute_graph_metrics(subject)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])