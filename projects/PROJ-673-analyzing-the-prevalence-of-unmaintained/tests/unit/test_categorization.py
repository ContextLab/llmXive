"""
Unit tests for category assignment logic in src/analysis/categorizer.py.

Tests verify:
1. Keyword matching logic (framework, data, no match, weak match).
2. Topology fallback logic (degree centrality, betweenness centrality).
3. Batch classification.
4. Graph building and distribution calculation.
5. Edge cases: missing keywords, noisy keywords, isolated nodes.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, List
import networkx as nx

from src.analysis.categorizer import (
    classify_by_keywords,
    classify_package,
    classify_batch,
    build_dependency_graph,
    get_category_distribution
)


# --- Keyword Matching Tests ---

def test_classify_by_keywords_framework():
    """Test classification of a framework package."""
    package_data = {
        "name": "express",
        "keywords": ["framework", "web", "server"]
    }
    result = classify_by_keywords(package_data)
    assert result == "framework", f"Expected 'framework', got '{result}'"

def test_classify_by_keywords_data():
    """Test classification of a data processing package."""
    package_data = {
        "name": "lodash",
        "keywords": ["data", "utilities", "functional"]
    }
    result = classify_by_keywords(package_data)
    assert result == "data", f"Expected 'data', got '{result}'"

def test_classify_by_keywords_no_match():
    """Test classification when no keywords match known categories."""
    package_data = {
        "name": "some-utility",
        "keywords": ["helper", "misc", "tool"]
    }
    result = classify_by_keywords(package_data)
    assert result == "other", f"Expected 'other', got '{result}'"

def test_classify_by_keywords_weak_match():
    """Test classification with ambiguous keywords (should fall back or default)."""
    # Assuming 'utils' is not a strong keyword for 'framework' or 'data'
    package_data = {
        "name": "generic-utils",
        "keywords": ["utils", "helper"]
    }
    result = classify_by_keywords(package_data)
    assert result == "other", f"Expected 'other' for weak match, got '{result}'"

def test_classify_package_with_keywords():
    """Test classify_package when keywords are present and match."""
    package_data = {
        "name": "react",
        "keywords": ["framework", "ui", "frontend"]
    }
    # Mock the topology calculation to ensure it's not called if keywords match
    with patch('src.analysis.categorizer._calculate_topology_metrics') as mock_topology:
        result = classify_package(package_data)
        mock_topology.assert_not_called()
        assert result == "framework"

def test_classify_package_fallback_to_topology():
    """Test classify_package when keywords are missing/noisy, falling back to topology."""
    package_data = {
        "name": "unknown-pkg",
        "keywords": []  # No keywords
    }
    mock_graph = MagicMock(spec=nx.Graph)
    mock_graph.nodes.return_value = ["unknown-pkg"]
    
    # Mock the graph building to return our mock graph
    with patch('src.analysis.categorizer.build_dependency_graph', return_value=mock_graph):
        # Mock the centrality calculations
        with patch('src.analysis.categorizer.nx.degree_centrality', return_value={"unknown-pkg": 0.9}):
            with patch('src.analysis.categorizer.nx.betweenness_centrality', return_value={"unknown-pkg": 0.1}):
                result = classify_package(package_data)
                assert result == "core", f"Expected 'core' based on degree > 0.8, got '{result}'"

def test_classify_package_with_topology():
    """Test classify_package with specific topology metrics."""
    package_data = {
        "name": "infra-pkg",
        "keywords": []
    }
    mock_graph = MagicMock(spec=nx.Graph)
    mock_graph.nodes.return_value = ["infra-pkg"]
    
    with patch('src.analysis.categorizer.build_dependency_graph', return_value=mock_graph):
        with patch('src.analysis.categorizer.nx.degree_centrality', return_value={"infra-pkg": 0.5}):
            with patch('src.analysis.categorizer.nx.betweenness_centrality', return_value={"infra-pkg": 0.6}):
                result = classify_package(package_data)
                assert result == "infrastructure", f"Expected 'infrastructure' based on betweenness > 0.5, got '{result}'"

def test_classify_batch():
    """Test batch classification of multiple packages."""
    packages = [
        {"name": "pkg1", "keywords": ["framework"]},
        {"name": "pkg2", "keywords": ["data"]},
        {"name": "pkg3", "keywords": []}
    ]
    # Mock topology for the third package
    mock_graph = MagicMock(spec=nx.Graph)
    mock_graph.nodes.return_value = ["pkg3"]
    
    with patch('src.analysis.categorizer.build_dependency_graph', return_value=mock_graph):
        with patch('src.analysis.categorizer.nx.degree_centrality', return_value={"pkg3": 0.9}):
            with patch('src.analysis.categorizer.nx.betweenness_centrality', return_value={"pkg3": 0.1}):
                results = classify_batch(packages)
    
    assert len(results) == 3
    assert results[0]["category"] == "framework"
    assert results[1]["category"] == "data"
    assert results[2]["category"] == "core"

# --- Graph Building and Distribution Tests ---

def test_build_dependency_graph():
    """Test building a dependency graph from a list of dependencies."""
    dependencies = [
        {"name": "pkg-a", "dependencies": ["pkg-b", "pkg-c"]},
        {"name": "pkg-b", "dependencies": ["pkg-c"]},
        {"name": "pkg-c", "dependencies": []}
    ]
    graph = build_dependency_graph(dependencies)
    
    assert isinstance(graph, nx.Graph)
    assert graph.has_node("pkg-a")
    assert graph.has_node("pkg-b")
    assert graph.has_node("pkg-c")
    assert graph.has_edge("pkg-a", "pkg-b")
    assert graph.has_edge("pkg-a", "pkg-c")
    assert graph.has_edge("pkg-b", "pkg-c")

def test_get_category_distribution():
    """Test calculation of category distribution."""
    categorized_packages = [
        {"name": "pkg1", "category": "framework"},
        {"name": "pkg2", "category": "framework"},
        {"name": "pkg3", "category": "data"},
        {"name": "pkg4", "category": "other"}
    ]
    distribution = get_category_distribution(categorized_packages)
    
    assert distribution == {
        "framework": 2,
        "data": 1,
        "other": 1
    }

# --- Edge Case Tests ---

def test_classify_package_with_missing_keywords():
    """Test classification when keywords field is missing entirely."""
    package_data = {
        "name": "no-keywords-pkg"
        # No 'keywords' key
    }
    mock_graph = MagicMock(spec=nx.Graph)
    mock_graph.nodes.return_value = ["no-keywords-pkg"]
    
    with patch('src.analysis.categorizer.build_dependency_graph', return_value=mock_graph):
        with patch('src.analysis.categorizer.nx.degree_centrality', return_value={"no-keywords-pkg": 0.5}):
            with patch('src.analysis.categorizer.nx.betweenness_centrality', return_value={"no-keywords-pkg": 0.5}):
                result = classify_package(package_data)
                # Should fall back to topology
                assert result in ["core", "infrastructure", "other"]

def test_classify_package_with_noisy_keywords():
    """Test classification when keywords are present but don't match any category."""
    package_data = {
        "name": "noisy-pkg",
        "keywords": ["noise", "random", "garbage"]
    }
    mock_graph = MagicMock(spec=nx.Graph)
    mock_graph.nodes.return_value = ["noisy-pkg"]
    
    with patch('src.analysis.categorizer.build_dependency_graph', return_value=mock_graph):
        with patch('src.analysis.categorizer.nx.degree_centrality', return_value={"noisy-pkg": 0.9}):
            with patch('src.analysis.categorizer.nx.betweenness_centrality', return_value={"noisy-pkg": 0.1}):
                result = classify_package(package_data)
                # Should fall back to topology because keywords didn't match
                assert result == "core"

def test_graph_metrics_calculation():
    """Test that graph metrics are calculated correctly for topology fallback."""
    # Create a small graph manually
    G = nx.Graph()
    G.add_edge("A", "B")
    G.add_edge("A", "C")
    G.add_edge("B", "C")
    G.add_edge("A", "D")
    
    degree = nx.degree_centrality(G)
    betweenness = nx.betweenness_centrality(G)
    
    # A is connected to B, C, D -> degree should be higher
    assert degree["A"] > degree["B"]
    assert degree["A"] > degree["D"]
    
    # A is a central node, so betweenness should be non-zero
    assert betweenness["A"] > 0.0

def test_topology_classification_isolated():
    """Test classification of an isolated node (no dependencies)."""
    package_data = {
        "name": "isolated-pkg",
        "keywords": []
    }
    mock_graph = MagicMock(spec=nx.Graph)
    mock_graph.nodes.return_value = ["isolated-pkg"]
    mock_graph.edges.return_value = []
    
    with patch('src.analysis.categorizer.build_dependency_graph', return_value=mock_graph):
        with patch('src.analysis.categorizer.nx.degree_centrality', return_value={"isolated-pkg": 0.0}):
            with patch('src.analysis.categorizer.nx.betweenness_centrality', return_value={"isolated-pkg": 0.0}):
                result = classify_package(package_data)
                # Should be 'other' as it doesn't meet core or infrastructure thresholds
                assert result == "other"

def test_topology_classification_high_degree():
    """Test classification of a node with very high degree centrality."""
    package_data = {
        "name": "high-degree-pkg",
        "keywords": []
    }
    mock_graph = MagicMock(spec=nx.Graph)
    mock_graph.nodes.return_value = ["high-degree-pkg"]
    
    with patch('src.analysis.categorizer.build_dependency_graph', return_value=mock_graph):
        with patch('src.analysis.categorizer.nx.degree_centrality', return_value={"high-degree-pkg": 0.95}):
            with patch('src.analysis.categorizer.nx.betweenness_centrality', return_value={"high-degree-pkg": 0.05}):
                result = classify_package(package_data)
                assert result == "core", f"Expected 'core' for high degree, got '{result}'"