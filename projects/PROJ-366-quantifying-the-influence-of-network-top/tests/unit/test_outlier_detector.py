"""
Unit tests for outlier detection functionality.
"""
import json
import pickle
import tempfile
from pathlib import Path
import pytest
import numpy as np

from code.analysis.outlier_detector import (
    load_graph_metrics,
    extract_node_degrees,
    calculate_defect_ratio,
    detect_outliers,
    write_excluded_samples
)

@pytest.fixture
def sample_graph_good():
    """Create a sample graph with normal coordination (all nodes degree 4)."""
    return {
        "graph_id": "sample_good",
        "nodes": [
            {"id": i, "coords": [0.0, 0.0, 0.0], "degree": 4, "clustering_coeff": 0.5}
            for i in range(100)
        ],
        "edges": [[i, (i+1) % 100] for i in range(100)]
    }

@pytest.fixture
def sample_graph_outlier():
    """Create a sample graph with >15% defective nodes (coord < 3 or > 6)."""
    nodes = []
    # 20% defective nodes (20 out of 100)
    for i in range(100):
        if i < 20:
            # Defective: coordination < 3
            degree = 2
        else:
            degree = 4
        nodes.append({
            "id": i,
            "coords": [0.0, 0.0, 0.0],
            "degree": degree,
            "clustering_coeff": 0.5
        })
    
    return {
        "graph_id": "sample_outlier",
        "nodes": nodes,
        "edges": [[i, (i+1) % 100] for i in range(100)]
    }

@pytest.fixture
def sample_graph_high_defect():
    """Create a sample graph with >15% defective nodes (coord > 6)."""
    nodes = []
    # 20% defective nodes with high coordination
    for i in range(100):
        if i < 20:
            degree = 8  # > 6
        else:
            degree = 4
        nodes.append({
            "id": i,
            "coords": [0.0, 0.0, 0.0],
            "degree": degree,
            "clustering_coeff": 0.5
        })
    
    return {
        "graph_id": "sample_high_defect",
        "nodes": nodes,
        "edges": [[i, (i+1) % 100] for i in range(100)]
    }

@pytest.fixture
def graphs_dir(tmp_path, sample_graph_good, sample_graph_outlier, sample_graph_high_defect):
    """Create a temporary directory with sample graph files."""
    graphs = {
        "sample_good.pkl": sample_graph_good,
        "sample_outlier.pkl": sample_graph_outlier,
        "sample_high_defect.pkl": sample_graph_high_defect
    }
    
    for filename, graph_data in graphs.items():
        filepath = tmp_path / filename
        with open(filepath, 'wb') as f:
            pickle.dump(graph_data, f)
    
    return tmp_path

def test_extract_node_degrees(sample_graph_good):
    """Test extraction of node degrees from graph data."""
    degrees = extract_node_degrees(sample_graph_good)
    assert len(degrees) == 100
    assert all(d == 4 for d in degrees)

def test_calculate_defect_ratio_no_defects(sample_graph_good):
    """Test defect ratio calculation with no defective nodes."""
    degrees = extract_node_degrees(sample_graph_good)
    ratio = calculate_defect_ratio(degrees, min_coord=3, max_coord=6)
    assert ratio == 0.0

def test_calculate_defect_ratio_with_defects(sample_graph_outlier):
    """Test defect ratio calculation with 20% defective nodes."""
    degrees = extract_node_degrees(sample_graph_outlier)
    ratio = calculate_defect_ratio(degrees, min_coord=3, max_coord=6)
    assert ratio == 0.20  # 20 out of 100

def test_calculate_defect_ratio_empty_list():
    """Test defect ratio calculation with empty degree list."""
    ratio = calculate_defect_ratio([], min_coord=3, max_coord=6)
    assert ratio == 0.0

def test_detect_outliers_basic(graphs_dir, sample_graph_good, sample_graph_outlier, sample_graph_high_defect):
    """Test outlier detection with mixed good and bad samples."""
    graphs = load_graph_metrics(graphs_dir)
    assert len(graphs) == 3
    
    excluded = detect_outliers(graphs, defect_threshold=0.15)
    
    # Should exclude sample_outlier and sample_high_defect (both have 20% defects)
    assert "sample_outlier" in excluded
    assert "sample_high_defect" in excluded
    assert "sample_good" not in excluded

def test_detect_outliers_threshold_adjustment(graphs_dir, sample_graph_outlier):
    """Test outlier detection with adjusted threshold."""
    graphs = load_graph_metrics(graphs_dir)
    
    # With threshold 0.25, sample_outlier (20% defects) should NOT be excluded
    excluded_high = detect_outliers(graphs, defect_threshold=0.25)
    assert "sample_outlier" not in excluded_high
    
    # With threshold 0.15, sample_outlier (20% defects) SHOULD be excluded
    excluded_low = detect_outliers(graphs, defect_threshold=0.15)
    assert "sample_outlier" in excluded_low

def test_write_excluded_samples(tmp_path, graphs_dir):
    """Test writing excluded samples to JSON and log files."""
    graphs = load_graph_metrics(graphs_dir)
    excluded = detect_outliers(graphs, defect_threshold=0.15)
    
    output_path = tmp_path / "excluded_samples.json"
    defect_log_path = tmp_path / "defect_log.txt"
    
    write_excluded_samples(excluded, output_path, defect_log_path)
    
    # Verify JSON file
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert "excluded_samples" in data
    assert len(data["excluded_samples"]) == 2
    assert "sample_outlier" in data["excluded_samples"]
    assert "sample_high_defect" in data["excluded_samples"]
    
    # Verify log file
    assert defect_log_path.exists()
    with open(defect_log_path, 'r') as f:
        log_content = f.read()
    
    assert "Topological Defect Log" in log_content
    assert "sample_outlier" in log_content
    assert "sample_high_defect" in log_content

def test_write_excluded_samples_empty(tmp_path):
    """Test writing excluded samples when no outliers are found."""
    excluded = set()
    output_path = tmp_path / "excluded_samples.json"
    defect_log_path = tmp_path / "defect_log.txt"
    
    write_excluded_samples(excluded, output_path, defect_log_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data["count"] == 0
    assert data["excluded_samples"] == []

def test_coordination_boundary_conditions():
    """Test coordination number boundary conditions."""
    # Test with exactly min_coord (should be OK)
    degrees = [3, 4, 5, 6]
    ratio = calculate_defect_ratio(degrees, min_coord=3, max_coord=6)
    assert ratio == 0.0
    
    # Test with exactly max_coord (should be OK)
    degrees = [3, 4, 5, 6]
    ratio = calculate_defect_ratio(degrees, min_coord=3, max_coord=6)
    assert ratio == 0.0
    
    # Test with min_coord - 1 (should be defective)
    degrees = [2, 4, 5, 6]
    ratio = calculate_defect_ratio(degrees, min_coord=3, max_coord=6)
    assert ratio == 0.25
    
    # Test with max_coord + 1 (should be defective)
    degrees = [3, 4, 5, 7]
    ratio = calculate_defect_ratio(degrees, min_coord=3, max_coord=6)
    assert ratio == 0.25
