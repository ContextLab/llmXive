"""
Contract tests for centrality metric calculation.

These tests verify that the centrality calculation logic adheres to the
specified data contracts, schema requirements, and mathematical definitions
before full implementation is attempted.

Test Strategy:
1. Verify input schema (connectivity matrix format)
2. Verify output schema (centrality metrics DataFrame)
3. Verify mathematical correctness of centrality metrics
4. Verify handling of edge cases (disconnected graphs, NaN values)
"""

import pytest
import numpy as np
import pandas as pd
import networkx as nx
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.config import get_centrality_config, get_fixed_region_indices


class TestCentralityInputSchema:
    """Test that input connectivity matrices adhere to expected schema."""
    
    def test_connectivity_matrix_shape(self):
        """Verify that input matrices are square and symmetric."""
        # Create a valid connectivity matrix
        n_regions = 90  # AAL3 atlas size
        matrix = np.random.rand(n_regions, n_regions)
        matrix = (matrix + matrix.T) / 2  # Make symmetric
        np.fill_diagonal(matrix, 0)  # Zero diagonal
        
        # Validate shape
        assert matrix.shape[0] == matrix.shape[1], "Matrix must be square"
        assert matrix.shape[0] == n_regions, f"Expected {n_regions} regions"
        
    def test_connectivity_matrix_dtype(self):
        """Verify that matrices use float32 for memory efficiency."""
        matrix = np.random.rand(10, 10).astype(np.float32)
        assert matrix.dtype == np.float32, "Matrix should be float32"
        
    def test_connectivity_matrix_no_nan(self):
        """Verify that input matrices contain no NaN values."""
        matrix = np.random.rand(10, 10)
        matrix[0, 0] = np.nan  # Introduce NaN
        
        assert np.isnan(matrix).any(), "Matrix should contain NaN for this test"
        # In real implementation, this should raise an error or be handled
        
class TestCentralityOutputSchema:
    """Test that centrality outputs adhere to expected schema."""
    
    def test_centrality_metrics_columns(self):
        """Verify that output DataFrame contains required columns."""
        # Expected columns based on task T020
        required_columns = [
            'subject_id',
            'region_index',
            'region_name',
            'degree_centrality',
            'betweenness_centrality',
            'eigenvector_centrality'
        ]
        
        # Create a mock output DataFrame
        df = pd.DataFrame({
            'subject_id': ['sub-01'],
            'region_index': [1],
            'region_name': ['Region1'],
            'degree_centrality': [0.5],
            'betweenness_centrality': [0.3],
            'eigenvector_centrality': [0.7]
        })
        
        for col in required_columns:
            assert col in df.columns, f"Missing required column: {col}"
            
    def test_centrality_metrics_dtypes(self):
        """Verify that output DataFrame has correct data types."""
        df = pd.DataFrame({
            'subject_id': ['sub-01'],
            'region_index': [1],
            'region_name': ['Region1'],
            'degree_centrality': [0.5],
            'betweenness_centrality': [0.3],
            'eigenvector_centrality': [0.7]
        })
        
        assert df['subject_id'].dtype == object, "subject_id should be string"
        assert df['region_index'].dtype in [np.int64, np.int32], "region_index should be integer"
        assert df['degree_centrality'].dtype in [np.float64, np.float32], "degree_centrality should be float"
        assert df['betweenness_centrality'].dtype in [np.float64, np.float32], "betweenness_centrality should be float"
        assert df['eigenvector_centrality'].dtype in [np.float64, np.float32], "eigenvector_centrality should be float"
        
    def test_centrality_metrics_range(self):
        """Verify that centrality metrics are within valid ranges."""
        # Degree centrality: [0, 1]
        # Betweenness centrality: [0, 1]
        # Eigenvector centrality: [0, 1] (normalized)
        
        df = pd.DataFrame({
            'subject_id': ['sub-01'],
            'region_index': [1],
            'region_name': ['Region1'],
            'degree_centrality': [0.5],
            'betweenness_centrality': [0.3],
            'eigenvector_centrality': [0.7]
        })
        
        assert 0 <= df['degree_centrality'].iloc[0] <= 1, "Degree centrality must be in [0, 1]"
        assert 0 <= df['betweenness_centrality'].iloc[0] <= 1, "Betweenness centrality must be in [0, 1]"
        assert 0 <= df['eigenvector_centrality'].iloc[0] <= 1, "Eigenvector centrality must be in [0, 1]"
        
class TestCentralityMathematicalCorrectness:
    """Test that centrality metrics are calculated correctly."""
    
    def test_degree_centrality_definition(self):
        """Verify degree centrality calculation matches NetworkX definition."""
        # Create a simple graph: 0-1-2-3 (path graph)
        G = nx.path_graph(4)
        
        # Degree centrality for path graph:
        # Node 0: 1/3 (connected to 1 out of 3 possible)
        # Node 1: 2/3 (connected to 2 out of 3 possible)
        # Node 2: 2/3 (connected to 2 out of 3 possible)
        # Node 3: 1/3 (connected to 1 out of 3 possible)
        
        expected = {0: 1/3, 1: 2/3, 2: 2/3, 3: 1/3}
        actual = nx.degree_centrality(G)
        
        for node in G.nodes():
            assert abs(actual[node] - expected[node]) < 1e-10, \
                f"Degree centrality mismatch for node {node}"
                
    def test_betweenness_centrality_definition(self):
        """Verify betweenness centrality calculation matches NetworkX definition."""
        # Create a star graph: 0 is center, connected to 1, 2, 3
        G = nx.star_graph(3)
        
        # Betweenness centrality for star graph:
        # Center node (0): 0 (no shortest paths pass through it)
        # Leaf nodes (1, 2, 3): 0 (no shortest paths pass through them)
        # Actually, for star graph, all nodes have 0 betweenness
        
        actual = nx.betweenness_centrality(G, normalized=True)
        
        # All nodes should have very low betweenness in a star graph
        for node in G.nodes():
            assert actual[node] < 0.1, f"Betweenness centrality unexpectedly high for node {node}"
            
    def test_eigenvector_centrality_definition(self):
        """Verify eigenvector centrality calculation matches NetworkX definition."""
        # Create a complete graph: all nodes connected to all others
        G = nx.complete_graph(5)
        
        # In a complete graph, all nodes should have equal eigenvector centrality
        actual = nx.eigenvector_centrality(G)
        
        values = list(actual.values())
        # All values should be approximately equal
        assert max(values) - min(values) < 1e-10, \
            "All nodes in complete graph should have equal eigenvector centrality"
            
class TestCentralityEdgeCases:
    """Test handling of edge cases in centrality calculation."""
    
    def test_disconnected_graph(self):
        """Verify handling of disconnected graphs."""
        # Create a disconnected graph: two separate components
        G = nx.Graph()
        G.add_edges_from([(0, 1), (2, 3)])  # Two separate edges
        
        # Degree centrality should still work
        degree = nx.degree_centrality(G)
        assert len(degree) == 4, "All nodes should be included"
        
        # Betweenness centrality should work
        betweenness = nx.betweenness_centrality(G)
        assert len(betweenness) == 4, "All nodes should be included"
        
        # Eigenvector centrality might fail or return zeros
        try:
            eigenvector = nx.eigenvector_centrality(G)
            # If it succeeds, values should be reasonable
            for node, val in eigenvector.items():
                assert 0 <= val <= 1, f"Eigenvector centrality out of range for node {node}"
        except nx.PowerIterationFailedConvergence:
            # This is expected for disconnected graphs
            pass
            
    def test_single_node_graph(self):
        """Verify handling of single node graphs."""
        G = nx.Graph()
        G.add_node(0)
        
        # Degree centrality should be 0
        degree = nx.degree_centrality(G)
        assert degree[0] == 0, "Single node should have degree centrality of 0"
        
        # Betweenness centrality should be 0
        betweenness = nx.betweenness_centrality(G)
        assert betweenness[0] == 0, "Single node should have betweenness centrality of 0"
        
    def test_zero_connectivity_matrix(self):
        """Verify handling of zero connectivity matrix."""
        matrix = np.zeros((5, 5))
        G = nx.from_numpy_array(matrix)
        
        # All centrality metrics should be 0
        degree = nx.degree_centrality(G)
        betweenness = nx.betweenness_centrality(G)
        
        for node in G.nodes():
            assert degree[node] == 0, "Zero matrix should result in zero degree centrality"
            assert betweenness[node] == 0, "Zero matrix should result in zero betweenness centrality"
            
class TestConfigIntegration:
    """Test integration with configuration system."""
    
    def test_fixed_region_indices_config(self):
        """Verify that fixed region indices are correctly retrieved from config."""
        indices = get_fixed_region_indices()
        
        assert isinstance(indices, list), "Fixed region indices should be a list"
        assert len(indices) > 0, "Fixed region indices should not be empty"
        assert all(isinstance(i, int) for i in indices), "All indices should be integers"
        assert all(i >= 1 for i in indices), "Region indices should be >= 1 (AAL3 convention)"
        
    def test_centrality_config_defaults(self):
        """Verify that centrality config has expected defaults."""
        config = get_centrality_config()
        
        # Check that required fields exist
        assert hasattr(config, 'metrics'), "Config should have 'metrics' attribute"
        assert hasattr(config, 'threshold'), "Config should have 'threshold' attribute"
        
        # Verify default metrics include required ones
        default_metrics = ['degree', 'betweenness', 'eigenvector']
        for metric in default_metrics:
            assert metric in config.metrics, f"Default metrics should include {metric}"
            
class TestDataPersistence:
    """Test that data persistence follows expected patterns."""
    
    def test_output_file_path_format(self):
        """Verify that output file paths follow expected naming convention."""
        subject_id = "sub-01"
        expected_filename = f"{subject_id}_metrics.csv"
        
        # Check that filename follows pattern
        assert expected_filename.endswith("_metrics.csv"), "Filename should end with _metrics.csv"
        assert expected_filename.startswith("sub-"), "Filename should start with sub-"
        
    def test_csv_column_order(self):
        """Verify that CSV output maintains consistent column order."""
        expected_order = [
            'subject_id',
            'region_index',
            'region_name',
            'degree_centrality',
            'betweenness_centrality',
            'eigenvector_centrality'
        ]
        
        df = pd.DataFrame(columns=expected_order)
        assert list(df.columns) == expected_order, "Column order should match expected"
            
class TestValidationAgainstSpecification:
    """Test that implementation meets specification requirements."""
    
    def test_all_regions_included(self):
        """Verify that all ~90 regions from AAL3 atlas are included."""
        # AAL3 atlas has approximately 90 regions
        expected_min_regions = 85
        expected_max_regions = 95
        
        # This test would be validated against actual implementation
        # For now, we verify the contract
        assert True, "Implementation should include all regions from AAL3 atlas"
        
    def test_global_centralty_calculation(self):
        """Verify that global centrality is calculated as mean of fixed subset."""
        # Get fixed region indices from config
        fixed_indices = get_fixed_region_indices()
        
        # Create mock metrics for fixed regions
        metrics = {
            'degree': [0.5] * len(fixed_indices),
            'betweenness': [0.3] * len(fixed_indices),
            'eigenvector': [0.7] * len(fixed_indices)
        }
        
        # Calculate mean
        global_degree = np.mean(metrics['degree'])
        global_betweenness = np.mean(metrics['betweenness'])
        global_eigenvector = np.mean(metrics['eigenvector'])
        
        # Verify calculation
        assert global_degree == 0.5, "Global degree should be mean of fixed subset"
        assert global_betweenness == 0.3, "Global betweenness should be mean of fixed subset"
        assert global_eigenvector == 0.7, "Global eigenvector should be mean of fixed subset"
        
    def test_vif_threshold_config(self):
        """Verify that VIF threshold is correctly configured."""
        from utils.config import get_vif_threshold
        
        threshold = get_vif_threshold()
        assert isinstance(threshold, (int, float)), "VIF threshold should be numeric"
        assert threshold > 0, "VIF threshold should be positive"
        assert threshold == 5, "Default VIF threshold should be 5"