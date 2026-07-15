import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from analysis.fitting import fit_power_law_model, load_avalanche_sizes_from_store
from utils.logger import ResearchError

class TestPowerLawFittingEdgeCases:
    """Test edge cases for power-law model fitting as specified in T028."""

    def test_fitting_handles_empty_avalanche_sizes(self):
        """Test that fitting fails gracefully when avalanche sizes list is empty."""
        # Empty list should raise an error or return a specific failure status
        # We expect the function to handle this case without crashing the pipeline
        empty_sizes = np.array([])
        
        with pytest.raises((ValueError, ResearchError, IndexError)):
            fit_power_law_model(empty_sizes)

    def test_fitting_handles_single_avalanche(self):
        """Test fitting with only one avalanche event (insufficient for statistics)."""
        single_size = np.array([5.0])
        
        # Single point cannot fit a distribution
        with pytest.raises((ValueError, ResearchError)):
            fit_power_law_model(single_size)

    def test_fitting_handles_all_zeros(self):
        """Test fitting when all avalanche sizes are zero."""
        zero_sizes = np.array([0.0, 0.0, 0.0, 0.0])
        
        with pytest.raises((ValueError, ResearchError)):
            fit_power_law_model(zero_sizes)

    def test_fitting_handles_non_positive_values(self):
        """Test fitting when sizes contain negative or non-positive values."""
        invalid_sizes = np.array([1.0, -2.0, 0.0, 5.0])
        
        with pytest.raises((ValueError, ResearchError)):
            fit_power_law_model(invalid_sizes)

    def test_fitting_convergence_failure_on_uniform_data(self):
        """Test that fitting detects convergence failure on uniform data."""
        # Uniform data (all same value) often causes power-law fitting to fail
        uniform_sizes = np.array([3.0, 3.0, 3.0, 3.0, 3.0, 3.0])
        
        # Should raise an error or return a failure status
        with pytest.raises((ValueError, ResearchError)):
            fit_power_law_model(uniform_sizes)

    def test_fitting_handles_extreme_outliers(self):
        """Test fitting with extreme outliers that might break convergence."""
        extreme_sizes = np.array([1.0, 2.0, 1.0, 1.0, 1000000.0, 1.0])
        
        # Should either fit or raise a specific error about convergence
        result = fit_power_law_model(extreme_sizes)
        # If it doesn't raise, it should return a result indicating failure
        assert result is not None

    def test_fitting_handles_very_large_dataset(self):
        """Test fitting with a large number of samples to ensure no memory issues."""
        # Generate a reasonable power-law distributed dataset
        np.random.seed(42)
        large_sizes = np.random.pareto(a=2.5, size=10000) + 1  # Shift to positive
        
        # Should complete without error
        result = fit_power_law_model(large_sizes)
        assert result is not None

class TestDisconnectedGraphs:
    """Test edge cases for metrics computation on disconnected graphs."""

    def test_degree_centrality_on_disconnected_graph(self):
        """Test that degree centrality works on disconnected graph components."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
        from analysis.metrics import compute_degree_centrality
        
        # Create a disconnected graph: two separate triangles
        # Nodes 0,1,2 form one component; 3,4,5 form another
        adjacency = np.array([
            [0, 1, 1, 0, 0, 0],
            [1, 0, 1, 0, 0, 0],
            [1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 1],
            [0, 0, 0, 1, 0, 1],
            [0, 0, 0, 1, 1, 0]
        ])
        
        # Should not crash
        degree = compute_degree_centrality(adjacency)
        assert degree is not None
        assert len(degree) == 6

    def test_clustering_coefficient_on_disconnected_graph(self):
        """Test clustering coefficient on disconnected graph."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
        from analysis.metrics import compute_clustering_coefficient
        
        adjacency = np.array([
            [0, 1, 1, 0, 0, 0],
            [1, 0, 1, 0, 0, 0],
            [1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 1],
            [0, 0, 0, 1, 0, 1],
            [0, 0, 0, 1, 1, 0]
        ])
        
        clustering = compute_clustering_coefficient(adjacency)
        assert clustering is not None
        assert len(clustering) == 6

    def test_rich_club_on_disconnected_graph(self):
        """Test rich-club coefficient on disconnected graph."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
        from analysis.metrics import compute_rich_club_coefficient
        
        adjacency = np.array([
            [0, 1, 1, 0, 0, 0],
            [1, 0, 1, 0, 0, 0],
            [1, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 1],
            [0, 0, 0, 1, 0, 1],
            [0, 0, 0, 1, 1, 0]
        ])
        
        rich_club = compute_rich_club_coefficient(adjacency)
        assert rich_club is not None

    def test_metrics_on_single_node_graph(self):
        """Test metrics on a graph with only one node (edge case)."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
        from analysis.metrics import compute_degree_centrality, compute_clustering_coefficient
        
        adjacency = np.array([[0]])
        
        degree = compute_degree_centrality(adjacency)
        assert degree is not None
        assert len(degree) == 1

    def test_metrics_on_empty_graph(self):
        """Test metrics on a graph with no edges."""
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent / "code"))
        from analysis.metrics import compute_degree_centrality, compute_clustering_coefficient
        
        # 3 nodes, no edges
        adjacency = np.array([
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ])
        
        degree = compute_degree_centrality(adjacency)
        assert degree is not None
        assert all(d == 0 for d in degree)
        
        clustering = compute_clustering_coefficient(adjacency)
        assert clustering is not None
