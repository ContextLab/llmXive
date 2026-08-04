import pytest
import os
import sys
import json
from pathlib import Path
from scripts.extract_features import (
    get_cyclomatic_complexity,
    get_dependency_depth,
    get_lines_of_code,
    calculate_semantic_complexity_score,
    extract_graph_and_metrics,
    serialize_graph
)

# Test code snippets
SIMPLE_CODE = """
def hello():
    print("Hello")
"""

COMPLEX_CODE = """
def process(data):
    if data:
        for item in data:
            if item > 0:
                print(item)
            else:
                print("Negative")
    return data
"""

EMPTY_CODE = ""

NO_SEMANTIC_CODE = """
x = 1
y = 2
"""

def test_get_lines_of_code():
    assert get_lines_of_code(SIMPLE_CODE) == 3
    assert get_lines_of_code(COMPLEX_CODE) == 8
    assert get_lines_of_code(EMPTY_CODE) == 0
    assert get_lines_of_code("   \n  \n") == 0

def test_get_cyclomatic_complexity():
    # Simple function has base complexity 1
    assert get_cyclomatic_complexity(SIMPLE_CODE) == 1.0
    # Complex function has if/else/for loops increasing complexity
    cc = get_cyclomatic_complexity(COMPLEX_CODE)
    assert cc > 1.0

def test_get_dependency_depth():
    depth = get_dependency_depth(SIMPLE_CODE)
    assert depth > 0
    depth_empty = get_dependency_depth(EMPTY_CODE)
    assert depth_empty == 0

def test_calculate_semantic_complexity_score():
    score = calculate_semantic_complexity_score(SIMPLE_CODE)
    assert score is not None
    assert score > 0

    # Code with no functions/classes/calls
    score_empty = calculate_semantic_complexity_score(NO_SEMANTIC_CODE)
    assert score_empty is None

def test_extract_graph_and_metrics():
    graph, metrics = extract_graph_and_metrics(SIMPLE_CODE)
    
    # Check metrics presence
    assert "lines_of_code" in metrics
    assert "cyclomatic_complexity" in metrics
    assert "dependency_depth" in metrics
    assert "semantic_complexity_score" in metrics
    
    # Check graph structure
    assert "nodes" in graph
    assert "edges" in graph
    assert "metadata" in graph
    assert graph["metadata"]["has_semantic_nodes"] == True

def test_extract_graph_no_semantic():
    graph, metrics = extract_graph_and_metrics(NO_SEMANTIC_CODE)
    assert graph["metadata"]["has_semantic_nodes"] == False
    assert graph["metadata"]["fallback_active"] == True
    assert metrics["semantic_complexity_score"] is None

def test_serialize_graph(tmp_path):
    graph = {
        "nodes": [{"id": 1, "type": "test"}],
        "edges": [],
        "metadata": {}
    }
    output_path = tmp_path / "test_graph.json"
    serialize_graph(graph, str(output_path))
    
    assert output_path.exists()
    with open(output_path) as f:
        loaded = json.load(f)
    assert loaded["nodes"][0]["id"] == 1
