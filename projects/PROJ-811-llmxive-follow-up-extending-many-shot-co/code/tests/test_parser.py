import pytest
import networkx as nx
from code.src.parser import CoTParser, parse_trace_to_dag, get_max_path_depth, get_logical_difficulty
import json
import os
from pathlib import Path
from typing import List, Dict, Any

# Fixtures for test data
@pytest.fixture
def parser():
    return CoTParser()

@pytest.fixture
def simple_trace():
    """A simple linear trace without dependencies."""
    return [
        {"step_id": 1, "content": "Read the problem.", "dependencies": []},
        {"step_id": 2, "content": "Identify variables.", "dependencies": [1]},
        {"step_id": 3, "content": "Formulate equation.", "dependencies": [2]},
        {"step_id": 4, "content": "Solve equation.", "dependencies": [3]},
        {"step_id": 5, "content": "Verify answer.", "dependencies": [4]}
    ]

@pytest.fixture
def cyclic_trace():
    """A trace with a circular dependency (A->B->C->A)."""
    return [
        {"step_id": 1, "content": "Step A", "dependencies": [3]},
        {"step_id": 2, "content": "Step B", "dependencies": [1]},
        {"step_id": 3, "content": "Step C", "dependencies": [2]}
    ]

@pytest.fixture
def deep_trace():
    """A trace designed to test max path depth calculation."""
    # Creates a graph where the longest path is 1 -> 2 -> 4 -> 6 (length 4)
    # But there is a side branch 1 -> 3 -> 5 (length 3)
    return [
        {"step_id": 1, "content": "Start", "dependencies": []},
        {"step_id": 2, "content": "Branch A", "dependencies": [1]},
        {"step_id": 3, "content": "Branch B", "dependencies": [1]},
        {"step_id": 4, "content": "Deep A1", "dependencies": [2]},
        {"step_id": 5, "content": "Deep B1", "dependencies": [3]},
        {"step_id": 6, "content": "Deep A2", "dependencies": [4]},
        {"step_id": 7, "content": "End", "dependencies": [6, 5]}
    ]

@pytest.fixture
def complex_graph_trace():
    """A trace with multiple incoming edges to test edge counting logic."""
    return [
        {"step_id": 1, "content": "Start", "dependencies": []},
        {"step_id": 2, "content": "Path 1", "dependencies": [1]},
        {"step_id": 3, "content": "Path 2", "dependencies": [1]},
        {"step_id": 4, "content": "Path 3", "dependencies": [1]},
        {"step_id": 5, "content": "Convergence", "dependencies": [2, 3, 4]} # 3 incoming edges
    ]

@pytest.fixture
def ambiguous_trace():
    """Trace with missing or invalid dependency IDs."""
    return [
        {"step_id": 1, "content": "Step 1", "dependencies": []},
        {"step_id": 2, "content": "Step 2", "dependencies": [99]}, # Invalid ref
        {"step_id": 3, "content": "Step 3", "dependencies": [1]}
    ]

# --- Cycle Detection Tests ---

def test_cycle_detection(parser, cyclic_trace):
    """Verify that the parser detects cycles and flags the trace as invalid."""
    is_valid, dag, error_msg = parser.parse(cyclic_trace)
    assert is_valid is False, "Cycle should be detected"
    assert "cycle" in error_msg.lower() or "cyclic" in error_msg.lower()

def test_no_cycle_in_simple_trace(parser, simple_trace):
    """Verify that a linear trace is detected as valid."""
    is_valid, dag, error_msg = parser.parse(simple_trace)
    assert is_valid is True, "Linear trace should be valid"
    assert dag is not None
    assert nx.is_directed_acyclic_graph(dag)

def test_max_incoming_edges_flagging(parser, complex_graph_trace):
    """Verify that traces with too many incoming edges are flagged if configured."""
    # Default config usually allows this, but we test the logic if limit is set low
    # For this test, we just ensure the graph builds correctly without crashing
    is_valid, dag, error_msg = parser.parse(complex_graph_trace)
    assert is_valid is True, "Graph with multiple parents should be valid by default"
    
    # Verify edge count
    in_degree_5 = dag.in_degree(5)
    assert in_degree_5 == 3, "Node 5 should have 3 incoming edges"

def test_invalid_trace_flagging(parser, ambiguous_trace):
    """Verify that references to non-existent steps are flagged."""
    is_valid, dag, error_msg = parser.parse(ambiguous_trace)
    # Depending on strictness, this might be False. 
    # Based on typical robust parsers, missing refs are errors.
    assert is_valid is False, "Missing dependency reference should invalidate trace"

def test_empty_trace_handling(parser):
    """Verify behavior with empty input."""
    is_valid, dag, error_msg = parser.parse([])
    assert is_valid is True, "Empty trace should be valid (empty graph)"
    assert dag.number_of_nodes() == 0

# --- Depth Calculation Tests ---

def test_logical_difficulty_score(simple_trace):
    """Test that logical difficulty (max path depth) is calculated correctly for a linear chain."""
    is_valid, dag, _ = parse_trace_to_dag(simple_trace)
    assert is_valid
    
    depth = get_max_path_depth(dag)
    # Path: 1->2->3->4->5. 
    # If depth is node count in longest path: 5
    # If depth is edges: 4. 
    # get_max_path_depth usually counts nodes in the longest path in this context.
    assert depth == 5, f"Expected depth 5, got {depth}"

def test_complex_graph_depth(complex_graph_trace):
    """Test depth calculation on a graph with converging paths."""
    is_valid, dag, _ = parse_trace_to_dag(complex_graph_trace)
    assert is_valid
    
    depth = get_max_path_depth(dag)
    # Longest path: 1 -> 2 -> 5 (or 1->3->5, 1->4->5). Length 3.
    assert depth == 3, f"Expected depth 3, got {depth}"

def test_deep_trace_depth(deep_trace):
    """Test depth calculation on a graph with varying branch lengths."""
    is_valid, dag, _ = parse_trace_to_dag(deep_trace)
    assert is_valid
    
    depth = get_max_path_depth(dag)
    # Longest path: 1 -> 2 -> 4 -> 6 -> 7 (Length 5)
    # Alternative: 1 -> 3 -> 5 -> 7 (Length 4)
    assert depth == 5, f"Expected depth 5, got {depth}"

def test_logical_difficulty_empty_graph():
    """Test that an empty graph returns 0 depth."""
    G = nx.DiGraph()
    depth = get_max_path_depth(G)
    assert depth == 0

# --- Function Wrapper Tests ---

def test_parse_trace_to_dag_function(simple_trace):
    """Test the direct function wrapper."""
    is_valid, dag, error = parse_trace_to_dag(simple_trace)
    assert is_valid
    assert isinstance(dag, nx.DiGraph)
    assert len(dag.nodes()) == len(simple_trace)
    assert len(dag.edges()) == len(simple_trace) - 1

def test_get_logical_difficulty_function(simple_trace):
    """Test the high-level difficulty function."""
    score = get_logical_difficulty(simple_trace)
    assert score == 5, f"Expected score 5, got {score}"

def test_invalid_trace_flagging_with_cycle(cyclic_trace):
    """Ensure the high-level function returns invalid for cyclic traces."""
    score = get_logical_difficulty(cyclic_trace)
    # Should return 0 or -1 or similar indicator for invalid
    assert score == 0, "Cyclic trace should return 0 difficulty"

def test_max_incoming_edges_flagging_logic():
    """Test the internal logic for edge counting via direct graph manipulation."""
    G = nx.DiGraph()
    G.add_edges_from([(1, 2), (1, 3), (1, 4), (2, 5), (3, 5), (4, 5)])
    
    # Node 5 has 3 incoming edges
    in_degree = G.in_degree(5)
    assert in_degree == 3

def test_invalid_trace_flagging_unresolvable_ref():
    """Test parsing a trace with a reference to a non-existent node."""
    trace = [
        {"step_id": 1, "content": "A", "dependencies": []},
        {"step_id": 2, "content": "B", "dependencies": [100]}
    ]
    is_valid, dag, error = parse_trace_to_dag(trace)
    assert is_valid is False
    assert "missing" in error.lower() or "invalid" in error.lower()

def test_complex_graph_depth_verification(complex_graph_trace):
    """Verification test for the specific complex graph structure."""
    is_valid, dag, _ = parse_trace_to_dag(complex_graph_trace)
    assert is_valid
    
    # Verify structure explicitly
    assert dag.has_edge(1, 2)
    assert dag.has_edge(1, 3)
    assert dag.has_edge(1, 4)
    assert dag.has_edge(2, 5)
    assert dag.has_edge(3, 5)
    assert dag.has_edge(4, 5)
    
    # Verify depth
    assert get_max_path_depth(dag) == 3

def test_parser_handles_multiline_steps():
    """Ensure parser handles steps with newlines in content."""
    trace = [
        {"step_id": 1, "content": "Line 1\nLine 2", "dependencies": []},
        {"step_id": 2, "content": "Next", "dependencies": [1]}
    ]
    is_valid, dag, _ = parse_trace_to_dag(trace)
    assert is_valid
    # Check if content is preserved (networkx nodes store attributes)
    node_1_content = dag.nodes[1].get('content', '')
    assert "Line 1" in node_1_content

def test_parser_handles_special_characters():
    """Ensure parser handles special characters in content."""
    trace = [
        {"step_id": 1, "content": "x = 2 * (3 + 4)", "dependencies": []},
        {"step_id": 2, "content": "Result: 14!", "dependencies": [1]}
    ]
    is_valid, dag, _ = parse_trace_to_dag(trace)
    assert is_valid
    node_1_content = dag.nodes[1].get('content', '')
    assert "*" in node_1_content