import pytest
import pickle
from pathlib import Path
from data.graph_utils import build_adjacency_index, build_route_graph, validate_graph_against_ground_truth

class TestBuildAdjacencyIndex:
    def test_build_adjacency_index_basic(self):
        """Test basic adjacency index construction."""
        graph = {
            1: {2, 3, 4},
            2: {1, 3},
            3: {1, 2, 4},
            4: {1, 3}
        }
        
        index = build_adjacency_index(graph, top_n=2)
        
        assert 1 in index
        assert len(index[1]) == 2
        assert all(isinstance(neighbor, int) for neighbor, _ in index[1])
        assert all(isinstance(score, float) for _, score in index[1])
    
    def test_build_adjacency_index_empty_graph(self):
        """Test with empty graph."""
        graph = {}
        index = build_adjacency_index(graph, top_n=5)
        assert index == {}
    
    def test_build_adjacency_index_top_n_limit(self):
        """Test that top_n limit is respected."""
        graph = {
            1: {2, 3, 4, 5, 6, 7, 8, 9, 10}
        }
        
        index = build_adjacency_index(graph, top_n=3)
        assert len(index[1]) == 3
    
    def test_build_adjacency_index_deterministic_order(self):
        """Test that tie-breaking produces deterministic order."""
        graph = {
            1: {5, 2, 8, 1}  # Note: 1 in neighbors is self-loop, should be handled
        }
        
        index = build_adjacency_index(graph, top_n=10)
        # Check that neighbors are sorted
        neighbors = [n for n, _ in index[1]]
        assert neighbors == sorted(neighbors)
    
    def test_adjacency_index_persistence(self):
        """Test that index can be pickled and unpickled."""
        graph = {
            1: {2, 3},
            2: {1, 3},
            3: {1, 2}
        }
        
        index = build_adjacency_index(graph, top_n=2)
        
        # Pickle and unpickle
        pickled = pickle.dumps(index)
        unpickled = pickle.loads(pickled)
        
        assert index == unpickled
    
    def test_adjacency_index_output_structure(self):
        """Test the structure of the adjacency index output."""
        graph = {
            1: {2, 3},
            2: {1, 3}
        }
        
        index = build_adjacency_index(graph, top_n=2)
        
        # Check structure
        assert isinstance(index, dict)
        for station_id, neighbors in index.items():
            assert isinstance(station_id, int)
            assert isinstance(neighbors, list)
            for neighbor, score in neighbors:
                assert isinstance(neighbor, int)
                assert isinstance(score, float)
                assert score == 1.0  # Unweighted graph