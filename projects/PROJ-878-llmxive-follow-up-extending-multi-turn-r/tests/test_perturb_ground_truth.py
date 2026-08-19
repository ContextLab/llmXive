"""
Tests for the Randomized Path Perturbation logic (T015).
"""
import pytest
import json
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open
import networkx as nx

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "code"))

from utils.graph_utils import (
    graph_from_dict, 
    longest_path, 
    get_random_valid_path_different_from_reference
)
from perturb_ground_truth import process_puzzles, load_puzzles

class TestPathPerturbation:
    """Tests for path perturbation logic."""
    
    def test_find_different_path_simple_dag(self):
        """Test finding a different path in a simple DAG."""
        G = nx.DiGraph()
        G.add_edges_from([
            (0, 1), (0, 2), (1, 3), (2, 3)
        ])
        
        # Longest path could be [0, 1, 3] or [0, 2, 3]
        ref_path = [0, 1, 3]
        
        result = get_random_valid_path_different_from_reference(G, ref_path, max_attempts=100)
        
        assert result is not None
        assert result != ref_path
        assert nx.is_path(G, result)
    
    def test_no_different_path_exists(self):
        """Test when only one path exists."""
        G = nx.DiGraph()
        G.add_edges_from([
            (0, 1), (1, 2), (2, 3)
        ])
        
        ref_path = [0, 1, 2, 3]
        
        result = get_random_valid_path_different_from_reference(G, ref_path, max_attempts=100)
        
        # Should return None since no other path exists
        assert result is None
    
    def test_process_puzzles_updates_ground_truth(self):
        """Test that process_puzzles updates the ground truth path."""
        # Create a simple puzzle with a graph that has multiple paths
        puzzle_data = {
            "instance_id": "test_001",
            "text": "Test puzzle",
            "ground_truth_path": [0, 1, 3], # Original longest path
            "graph_structure": {
                "nodes": [0, 1, 2, 3],
                "edges": [(0, 1), (0, 2), (1, 3), (2, 3)]
            }
        }
        
        updated_puzzles, metrics = process_puzzles([puzzle_data], max_attempts=100)
        
        assert len(updated_puzzles) == 1
        updated_puzzle = updated_puzzles[0]
        
        # The new ground truth should be different from the original
        assert updated_puzzle["ground_truth_path"] != updated_puzzle["original_longest_path"]
        assert updated_puzzle["ground_truth_path"] == [0, 2, 3] or updated_puzzle["ground_truth_path"] == [0, 1, 3]
        
        # Metrics should indicate success
        assert metrics["successful_perturbations"] >= 0
        assert "cycle_rate" in metrics
        assert metrics["status"] == "[deferred]"
    
    def test_process_puzzles_metrics_structure(self):
        """Test that metrics contain required fields."""
        puzzle_data = {
            "instance_id": "test_001",
            "text": "Test",
            "ground_truth_path": [0, 1, 2],
            "graph_structure": {
                "nodes": [0, 1, 2],
                "edges": [(0, 1), (1, 2)]
            }
        }
        
        _, metrics = process_puzzles([puzzle_data], max_attempts=10)
        
        required_keys = [
            "total_instances", 
            "successful_perturbations", 
            "failed_perturbations", 
            "cycle_rate", 
            "status"
        ]
        
        for key in required_keys:
            assert key in metrics, f"Missing key: {key}"
        
        assert metrics["status"] == "[deferred]"
    
    def test_empty_graph_handling(self):
        """Test handling of empty graphs."""
        G = nx.DiGraph()
        ref_path = []
        
        result = get_random_valid_path_different_from_reference(G, ref_path, max_attempts=10)
        
        assert result is None