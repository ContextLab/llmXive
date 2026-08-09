import pytest
import numpy as np
import networkx as nx
from pathlib import Path
import sys
import os

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from graph_metrics import (
    compute_modularity_louvain,
    compute_modularity_with_resolution_sweep,
    generate_correlation_matrix
)

class TestModularityCalculation:
    
    def test_modularity_louvain_res1(self):
        """Test that modularity is calculated and returns a float."""
        # Create a mock correlation matrix (random)
        np.random.seed(42)
        n_rois = 50
        ts = np.random.randn(n_rois, 100)
        corr_mat = generate_correlation_matrix(ts)
        
        modularity = compute_modularity_louvain(corr_mat, resolution=1.0)
        
        assert modularity is not None
        assert isinstance(modularity, float)
        # Modularity typically ranges from -0.5 to 1.0, usually > 0 for real networks
        # We just assert it's a number for now.
        assert -1.0 < modularity < 1.0

    def test_modularity_resolution_sweep(self):
        """Test that resolution sweep returns a dict with expected keys."""
        np.random.seed(42)
        n_rois = 50
        ts = np.random.randn(n_rois, 100)
        corr_mat = generate_correlation_matrix(ts)
        
        resolutions = [0.5, 1.0, 1.5]
        results = compute_modularity_with_resolution_sweep(corr_mat, resolutions=resolutions)
        
        assert isinstance(results, dict)
        for res in resolutions:
            key = f"res_{res}"
            assert key in results
            # Value should be a float or None (if failed)
            if results[key] is not None:
                assert isinstance(results[key], float)

    def test_modularity_on_clustered_matrix(self):
        """Test modularity on a matrix with known community structure."""
        # Create a block-diagonal matrix (strong communities)
        n_per_block = 20
        n_blocks = 3
        size = n_per_block * n_blocks
        
        # Initialize with zeros
        corr_mat = np.zeros((size, size))
        
        # Fill blocks with high correlation
        for i in range(n_blocks):
            start = i * n_per_block
            end = (i + 1) * n_per_block
            corr_mat[start:end, start:end] = 0.8
            np.fill_diagonal(corr_mat[start:end, start:end], 0.0)
        
        # Add some noise
        noise = np.random.rand(size, size) * 0.1
        corr_mat = (corr_mat + noise) / (1 + noise) # Normalize roughly
        
        # Ensure symmetry
        corr_mat = (corr_mat + corr_mat.T) / 2
        
        modularity = compute_modularity_louvain(corr_mat, resolution=1.0)
        
        # For a clearly clustered matrix, modularity should be relatively high
        assert modularity > 0.3, f"Expected high modularity for clustered matrix, got {modularity}"

    def test_modularity_fallback_handling(self):
        """Test behavior when resolution sweep encounters issues."""
        # This test ensures the function doesn't crash on edge cases
        np.random.seed(42)
        n_rois = 10
        ts = np.random.randn(n_rois, 100)
        corr_mat = generate_correlation_matrix(ts)
        
        # Try a very high resolution which might lead to many small communities
        results = compute_modularity_with_resolution_sweep(corr_mat, resolutions=[5.0])
        
        assert "res_5.0" in results
        # Should not raise an exception

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
