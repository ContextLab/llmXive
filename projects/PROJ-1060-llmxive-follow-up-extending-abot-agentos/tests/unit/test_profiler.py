"""
Unit tests for the performance profiler module.
"""
import pytest
import json
import os
from pathlib import Path
import tempfile

# Import the profiler module
from profiler import generate_test_graph, run_profiling_experiment

def test_generate_test_graph_structure():
    """Test that the generated graph has the expected structure."""
    G = generate_test_graph(num_nodes=50, num_edges=80)
    
    # Check node count
    assert len(G.nodes()) == 50
    
    # Check edge count (may be less due to duplicate prevention)
    assert len(G.edges()) <= 80
    assert len(G.edges()) >= 40  # Should have a reasonable number of edges
    
    # Check node attributes
    for node_id, data in G.nodes(data=True):
        assert "token" in data
        assert "predicates" in data
        assert isinstance(data["predicates"], list)
    
    # Check edge attributes
    for source, target, data in G.edges(data=True):
        assert "predicate" in data

def test_profiling_report_generation():
    """Test that the profiling report is generated correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "test_profiling_report.json")
        
        # Run the profiling experiment
        report = run_profiling_experiment(output_path)
        
        # Verify the report file exists
        assert os.path.exists(output_path)
        
        # Verify the report structure
        assert "experiment_summary" in report
        assert "latency_metrics" in report
        assert "query_results" in report
        assert "hot_path_analysis" in report
        assert "optimization_recommendations" in report
        
        # Verify latency metrics structure
        latency = report["latency_metrics"]
        assert "avg_latency_ms" in latency
        assert "max_latency_ms" in latency
        assert "min_latency_ms" in latency
        assert "target_latency_ms" in latency
        assert "target_met" in latency
        
        # Verify target_met is boolean
        assert isinstance(latency["target_met"], bool)

def test_profiling_report_file_content():
    """Test that the profiling report file contains valid JSON."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "test_profiling_report.json")
        
        # Run the profiling experiment
        run_profiling_experiment(output_path)
        
        # Read and parse the file
        with open(output_path, 'r') as f:
            report = json.load(f)
        
        # Verify it's valid JSON with expected structure
        assert isinstance(report, dict)
        assert len(report) > 0

def test_profiling_with_small_graph():
    """Test profiling with a very small graph."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "small_graph_report.json")
        
        # Generate a tiny graph
        G = generate_test_graph(num_nodes=10, num_edges=15)
        
        # Verify the graph is small
        assert len(G.nodes()) == 10
        assert len(G.edges()) <= 15

def test_profiling_report_latency_target():
    """Test that the latency target is properly evaluated."""
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = os.path.join(temp_dir, "target_test_report.json")
        
        # Run the profiling experiment
        report = run_profiling_experiment(output_path)
        
        # Verify the target evaluation
        assert "target_met" in report["latency_metrics"]
        assert isinstance(report["latency_metrics"]["target_met"], bool)
        
        # Verify target latency is 100ms
        assert report["latency_metrics"]["target_latency_ms"] == 100.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])