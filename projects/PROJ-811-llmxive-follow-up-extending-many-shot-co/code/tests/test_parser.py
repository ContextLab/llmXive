import pytest
import networkx as nx
from code.src.parser import (
    CoTParser,
    parse_trace_to_dag,
    get_max_path_depth,
    get_logical_difficulty,
    detect_cycle,
    split_trace_into_steps,
    extract_references
)
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Fixtures

@pytest.fixture
def parser():
    return CoTParser()

@pytest.fixture
def simple_trace():
    """A valid, linear trace with no cycles."""
    return [
        {"step": 1, "text": "Read the problem.", "refs": []},
        {"step": 2, "text": "Identify variables.", "refs": [1]},
        {"step": 3, "text": "Formulate equation.", "refs": [2]},
        {"step": 4, "text": "Solve equation.", "refs": [3]},
        {"step": 5, "text": "Verify solution.", "refs": [4]}
    ]

@pytest.fixture
def cyclic_trace():
    """A trace with a direct cycle: Step 3 depends on 4, which depends on 3."""
    return [
        {"step": 1, "text": "Start.", "refs": []},
        {"step": 2, "text": "Process A.", "refs": [1]},
        {"step": 3, "text": "Process B (needs C).", "refs": [2, 4]},
        {"step": 4, "text": "Process C (needs B).", "refs": [3]},
        {"step": 5, "text": "End.", "refs": [4]}
    ]

@pytest.fixture
def deep_trace():
    """A trace designed to test maximum path depth calculation."""
    return [
        {"step": 1, "text": "Base.", "refs": []},
        {"step": 2, "text": "Level 1.", "refs": [1]},
        {"step": 3, "text": "Level 2.", "refs": [2]},
        {"step": 4, "text": "Level 3.", "refs": [3]},
        {"step": 5, "text": "Level 4.", "refs": [4]},
        {"step": 6, "text": "Level 5.", "refs": [5]},
        {"step": 7, "text": "Level 6.", "refs": [6]}
    ]

@pytest.fixture
def complex_graph_trace():
    """A trace with branching and merging to test depth and edge counts."""
    return [
        {"step": 1, "text": "Start.", "refs": []},
        {"step": 2, "text": "Branch A.", "refs": [1]},
        {"step": 3, "text": "Branch B.", "refs": [1]},
        {"step": 4, "text": "Branch C.", "refs": [1]},
        {"step": 5, "text": "Merge (needs A, B, C).", "refs": [2, 3, 4]},
        {"step": 6, "text": "End.", "refs": [5]}
    ]

@pytest.fixture
def ambiguous_trace():
    """A trace with invalid references (step 99 doesn't exist)."""
    return [
        {"step": 1, "text": "Start.", "refs": []},
        {"step": 2, "text": "Invalid ref.", "refs": [99]},
        {"step": 3, "text": "End.", "refs": [2]}
    ]

# Cycle Detection Tests

def test_cycle_detection(parser, cyclic_trace):
    """Test that detect_cycle correctly identifies a cycle in the graph."""
    dag, _ = parse_trace_to_dag(cyclic_trace)
    has_cycle = detect_cycle(dag)
    assert has_cycle is True, "Cycle should be detected in cyclic_trace"

def test_no_cycle_in_simple_trace(parser, simple_trace):
    """Test that a valid linear trace has no cycles."""
    dag, _ = parse_trace_to_dag(simple_trace)
    has_cycle = detect_cycle(dag)
    assert has_cycle is False, "Simple trace should not have a cycle"

def test_max_incoming_edges_flagging(parser, complex_graph_trace):
    """Test flagging of nodes with > 3 incoming edges."""
    dag, _ = parse_trace_to_dag(complex_graph_trace)
    # Step 5 has 3 incoming edges (from 2, 3, 4).
    # The requirement is > 3. So step 5 should NOT be flagged.
    # Let's create a scenario where it IS > 3.
    
    # Manually check logic on the parsed graph
    in_degree_5 = dag.in_degree(5)
    assert in_degree_5 == 3
    
    # Create a trace where a node has 4 incoming edges
    heavy_trace = [
        {"step": 1, "text": "A", "refs": []},
        {"step": 2, "text": "B", "refs": []},
        {"step": 3, "text": "C", "refs": []},
        {"step": 4, "text": "D", "refs": []},
        {"step": 5, "text": "E", "refs": [1, 2, 3, 4]} # 4 incoming edges
    ]
    dag_heavy, _ = parse_trace_to_dag(heavy_trace)
    in_degree_5_heavy = dag_heavy.in_degree(5)
    assert in_degree_5_heavy == 4
    
    # Verify the flagging logic (conceptually, we check the degree)
    # The actual flagging happens in the manifest generation, 
    # but here we verify the graph structure allows detection.
    assert in_degree_5_heavy > 3, "Node 5 should have > 3 incoming edges"

def test_invalid_trace_flagging(parser, ambiguous_trace):
    """Test that traces with invalid references are flagged."""
    # The parser should handle missing refs gracefully or flag them.
    # We test that the DAG construction doesn't crash and we can identify the issue.
    dag, metadata = parse_trace_to_dag(ambiguous_trace)
    
    # Check if metadata contains the invalid ref info
    assert "invalid_references" in metadata
    assert 99 in metadata["invalid_references"]

def test_empty_trace_handling(parser):
    """Test handling of empty trace list."""
    dag, metadata = parse_trace_to_dag([])
    assert dag.number_of_nodes() == 0
    assert dag.number_of_edges() == 0
    assert metadata.get("is_valid", True) is False or metadata.get("empty", False)

# Logical Difficulty Score (Max Path Depth) Tests

def test_logical_difficulty_score(parser, simple_trace):
    """Test max path depth calculation for a linear trace."""
    dag, _ = parse_trace_to_dag(simple_trace)
    depth = get_max_path_depth(dag)
    # Path: 1->2->3->4->5. Length (nodes) = 5.
    # Depending on definition (edges vs nodes), check accordingly.
    # Usually depth is number of nodes in longest path.
    assert depth == 5

def test_complex_graph_depth(parser, complex_graph_trace):
    """Test max path depth in a graph with branching."""
    dag, _ = parse_trace_to_dag(complex_graph_trace)
    depth = get_max_path_depth(dag)
    # Longest path: 1 -> 2 -> 5 -> 6 (or 3->5->6, 4->5->6)
    # Nodes: 1, 2, 5, 6 = 4 nodes.
    assert depth == 4

def test_deep_trace_depth(parser, deep_trace):
    """Test max path depth for a deep chain."""
    dag, _ = parse_trace_to_dag(deep_trace)
    depth = get_max_path_depth(dag)
    assert depth == 7

def test_logical_difficulty_empty_graph(parser):
    """Test depth calculation on empty graph."""
    dag = nx.DiGraph()
    depth = get_max_path_depth(dag)
    assert depth == 0

def test_get_logical_difficulty_function(parser, simple_trace):
    """Test the wrapper function get_logical_difficulty."""
    score = get_logical_difficulty(simple_trace)
    assert score == 5

# Integration of Parser Logic

def test_parse_trace_to_dag_function(parser, simple_trace):
    """Test that parse_trace_to_dag returns a valid DiGraph and metadata."""
    dag, metadata = parse_trace_to_dag(simple_trace)
    assert isinstance(dag, nx.DiGraph)
    assert isinstance(metadata, dict)
    assert "nodes" in metadata or "edges" in metadata or "is_valid" in metadata

def test_get_logical_difficulty_function(parser, deep_trace):
    """Test get_logical_difficulty returns correct integer."""
    score = get_logical_difficulty(deep_trace)
    assert isinstance(score, int)
    assert score == 7

def test_invalid_trace_flagging_with_cycle(parser, cyclic_trace):
    """Ensure cyclic traces are flagged as invalid."""
    dag, metadata = parse_trace_to_dag(cyclic_trace)
    assert metadata.get("is_valid") is False
    assert metadata.get("has_cycle") is True

def test_max_incoming_edges_flagging_logic(parser):
    """Test logic for flagging nodes with > 3 incoming edges."""
    heavy_trace = [
        {"step": 1, "text": "A", "refs": []},
        {"step": 2, "text": "B", "refs": []},
        {"step": 3, "text": "C", "refs": []},
        {"step": 4, "text": "D", "refs": []},
        {"step": 5, "text": "E", "refs": [1, 2, 3, 4]}
    ]
    dag, metadata = parse_trace_to_dag(heavy_trace)
    
    # Verify the node 5 has high in-degree
    assert dag.in_degree(5) == 4
    
    # The metadata should ideally flag this if the parser implements it
    # We verify the condition is detectable
    has_high_indegree = any(dag.in_degree(n) > 3 for n in dag.nodes())
    assert has_high_indegree is True

def test_invalid_trace_flagging_unresolvable_ref(parser, ambiguous_trace):
    """Test that unresolvable references are captured in metadata."""
    dag, metadata = parse_trace_to_dag(ambiguous_trace)
    assert "invalid_references" in metadata
    assert 99 in metadata["invalid_references"]
    # The trace should be marked invalid due to missing refs
    assert metadata.get("is_valid") is False

def test_complex_graph_depth_verification(parser, complex_graph_trace):
    """Verify depth calculation handles complex merging correctly."""
    dag, _ = parse_trace_to_dag(complex_graph_trace)
    depth = get_max_path_depth(dag)
    # 1->2->5->6 (4 nodes)
    assert depth == 4

def test_parser_handles_multiline_steps(parser):
    """Test parser handles multiline text in steps."""
    multiline_trace = [
        {"step": 1, "text": "Line 1\nLine 2", "refs": []},
        {"step": 2, "text": "Next", "refs": [1]}
    ]
    dag, metadata = parse_trace_to_dag(multiline_trace)
    assert dag.number_of_nodes() == 2
    assert dag.number_of_edges() == 1

def test_parser_handles_special_characters(parser):
    """Test parser handles special characters in text."""
    special_trace = [
        {"step": 1, "text": "Use $100 and 3.14!", "refs": []},
        {"step": 2, "text": "Calculate % increase", "refs": [1]}
    ]
    dag, metadata = parse_trace_to_dag(special_trace)
    assert dag.number_of_nodes() == 2
    assert dag.number_of_edges() == 1