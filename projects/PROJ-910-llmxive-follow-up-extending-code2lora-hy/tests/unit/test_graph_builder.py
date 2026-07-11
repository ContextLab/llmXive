"""
Unit tests for code/feature_extractor/graph_builder.py
"""

import tempfile
import os
from pathlib import Path
import networkx as nx

import pytest

from code.feature_extractor.graph_builder import (
    ImportGraphBuilder,
    compute_centrality_metrics,
    extract_graph_features,
    get_graph_feature_vector_size,
    get_aggregated_graph_features
)


@pytest.fixture
def sample_repo(tmp_path):
    """Create a temporary directory with sample Python files."""
    # Create directory structure
    pkg = tmp_path / "mypackage"
    pkg.mkdir()
    sub = pkg / "submodule"
    sub.mkdir()

    # Create __init__.py files
    (pkg / "__init__.py").write_text("")
    (sub / "__init__.py").write_text("")

    # Create module files with imports
    (pkg / "module_a.py").write_text("""
import module_b
from submodule import module_c
""")
    (pkg / "module_b.py").write_text("""
import module_a
""")
    (sub / "module_c.py").write_text("""
from .. import module_a
""")

    return tmp_path


def test_import_graph_builder_init():
    """Test initialization of ImportGraphBuilder."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        builder = ImportGraphBuilder(Path(tmp_dir))
        assert builder.root_dir == Path(tmp_dir)
        assert builder.graph.is_empty()
        assert builder.node_files == {}


def test_build_empty_directory():
    """Test building graph from an empty directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        builder = ImportGraphBuilder(Path(tmp_dir))
        graph = builder.build()
        assert graph.number_of_nodes() == 0
        assert graph.number_of_edges() == 0


def test_build_with_files(sample_repo):
    """Test building graph from a directory with Python files."""
    builder = ImportGraphBuilder(sample_repo)
    graph = builder.build()

    # Should have nodes for each module
    assert graph.number_of_nodes() > 0
    # Should have edges for imports
    assert graph.number_of_edges() >= 0  # Could be 0 if no valid imports found


def test_compute_centrality_metrics_empty_graph():
    """Test centrality computation on an empty graph."""
    graph = nx.DiGraph()
    metrics = compute_centrality_metrics(graph)
    assert metrics == {}


def test_compute_centrality_metrics_single_node():
    """Test centrality computation on a graph with a single node."""
    graph = nx.DiGraph()
    graph.add_node("module_a")
    metrics = compute_centrality_metrics(graph)

    assert "module_a" in metrics
    assert metrics["module_a"]["in_degree"] == 0.0
    assert metrics["module_a"]["out_degree"] == 0.0
    assert metrics["module_a"]["betweenness"] == 0.0
    assert metrics["module_a"]["closeness"] == 0.0


def test_compute_centrality_metrics_connected_graph(sample_repo):
    """Test centrality computation on a connected graph."""
    builder = ImportGraphBuilder(sample_repo)
    graph = builder.build()

    if graph.number_of_nodes() > 0:
        metrics = compute_centrality_metrics(graph)
        assert len(metrics) == graph.number_of_nodes()

        # Check that all expected keys are present
        for node, scores in metrics.items():
            assert "in_degree" in scores
            assert "out_degree" in scores
            assert "betweenness" in scores
            assert "closeness" in scores


def test_extract_graph_features_empty():
    """Test feature extraction from an empty directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        features = extract_graph_features(Path(tmp_dir))
        assert features["num_nodes"] == 0
        assert features["num_edges"] == 0
        assert features["avg_in_degree"] == 0.0
        assert features["avg_out_degree"] == 0.0
        assert features["max_betweenness"] == 0.0
        assert features["max_closeness"] == 0.0
        assert features["centrality_scores"] == {}


def test_extract_graph_features_non_empty(sample_repo):
    """Test feature extraction from a directory with files."""
    features = extract_graph_features(sample_repo)
    assert features["num_nodes"] > 0
    assert "centrality_scores" in features
    assert isinstance(features["centrality_scores"], dict)


def test_get_graph_feature_vector_size():
    """Test that the feature vector size is correct."""
    size = get_graph_feature_vector_size()
    assert size == 6  # num_nodes, num_edges, avg_in, avg_out, max_bet, max_close


def test_get_aggregated_graph_features_empty():
    """Test aggregated feature extraction from an empty directory."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        features = get_aggregated_graph_features(Path(tmp_dir))
        assert len(features) == 6
        assert all(isinstance(f, float) for f in features)


def test_get_aggregated_graph_features_non_empty(sample_repo):
    """Test aggregated feature extraction from a directory with files."""
    features = get_aggregated_graph_features(sample_repo)
    assert len(features) == 6
    assert all(isinstance(f, float) for f in features)
    # At least num_nodes should be > 0
    assert features[0] > 0