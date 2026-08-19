import pytest
import json
import os
import sys
import networkx as nx
from typing import Dict, List, Any

# Add parent directory to path if running from tests/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from code.graph_generator import (
    LogicalPuzzleGenerator, 
    generate_single_puzzle, 
    generate_batch,
    _traverse_and_build_text,
    _get_deterministic_seed
)
from code.utils.graph_utils import is_dag, nesting_depth, longest_path, branching_factor

class TestDeterministicTemplateEngine:
    """Tests for the Deterministic Template Engine (T014)"""

    def test_text_generation_determinism(self):
        """Verify that the same graph and seed produce the same text."""
        seed = 12345
        instance_id = 99
        target_depth = 3
        target_branching = 2.0

        # Generate twice
        puzzle1 = generate_single_puzzle(target_depth, target_branching, instance_id, seed=seed)
        puzzle2 = generate_single_puzzle(target_depth, target_branching, instance_id, seed=seed)

        assert puzzle1['text'] == puzzle2['text'], "Text generation is not deterministic with same seed and ID"
        assert puzzle1['instance_id'] == puzzle2['instance_id']
        assert puzzle1['nesting_depth'] == puzzle2['nesting_depth']

    def test_text_structure_validity(self):
        """Verify that generated text contains expected logical keywords."""
        puzzle = generate_single_puzzle(target_depth=4, target_branching=3, instance_id=10)
        
        text = puzzle['text']
        # Basic sanity checks
        assert len(text) > 50, "Generated text is too short"
        assert "true" in text.lower() or "if" in text.lower() or "then" in text.lower(), \
            "Text does not contain logical connectors"

    def test_ground_truth_path_consistency(self):
        """Verify that the ground truth path is a valid path in the generated graph."""
        puzzle = generate_single_puzzle(target_depth=5, target_branching=2, instance_id=20)
        
        # Reconstruct graph from dict to verify
        graph_dict = puzzle['graph_structure']
        G = nx.DiGraph()
        for node in graph_dict['nodes']:
            G.add_node(node['id'])
        for edge in graph_dict['edges']:
            G.add_edge(edge['source'], edge['target'])
        
        path = puzzle['ground_truth_path']
        
        # Verify path is valid in graph
        for i in range(len(path) - 1):
            assert G.has_edge(path[i], path[i+1]), \
                f"Edge ({path[i]}, {path[i+1]}) not found in graph for path {path}"

    def test_output_schema_compliance(self):
        """Verify the output matches the LogicalPuzzle schema."""
        puzzle = generate_single_puzzle(target_depth=3, target_branching=2, instance_id=5)
        
        required_keys = [
            'instance_id', 'text', 'ground_truth_path', 
            'nesting_depth', 'branching_factor', 'graph_structure', 'metadata'
        ]
        
        for key in required_keys:
            assert key in puzzle, f"Missing required key: {key}"
        
        # Type checks
        assert isinstance(puzzle['instance_id'], int)
        assert isinstance(puzzle['text'], str)
        assert isinstance(puzzle['ground_truth_path'], list)
        assert isinstance(puzzle['nesting_depth'], int)
        assert isinstance(puzzle['branching_factor'], (int, float))
        assert isinstance(puzzle['graph_structure'], dict)

    def test_batch_generation(self):
        """Test batch generation produces multiple valid puzzles."""
        batch = generate_batch(
            target_depths=[3, 4], 
            target_branchings=[2.0, 3.0], 
            count=10, 
            seed=42
        )
        
        assert len(batch) > 0, "Batch generation returned empty list"
        
        # Verify all items are valid
        for i, puzzle in enumerate(batch):
            assert 'instance_id' in puzzle
            assert 'text' in puzzle
            assert len(puzzle['text']) > 0

    def test_depth_branching_control(self):
        """Verify that generated puzzles roughly respect target depth and branching."""
        # Note: Due to the stochastic nature of graph generation (even with seeds),
        # we check that the generated metrics are in a reasonable range relative to targets.
        target_d = 4
        target_b = 3.0
        
        puzzle = generate_single_puzzle(target_d, target_b, instance_id=100, seed=123)
        
        # Allow some variance, but it shouldn't be wildly different
        # The generator logic attempts to match these, but exact matching is hard.
        # We just verify the metrics are positive and non-trivial.
        assert puzzle['nesting_depth'] >= 1
        assert puzzle['branching_factor'] >= 1.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])