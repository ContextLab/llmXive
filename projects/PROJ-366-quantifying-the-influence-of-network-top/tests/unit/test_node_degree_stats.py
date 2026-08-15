import json
import os
import tempfile
from pathlib import Path
from collections import Counter
import pytest

from ingest.node_degree_stats_generator import (
    calculate_global_degree_distribution,
    compute_mode_and_stats,
    validate_mode_for_amorphous_silicon,
    main
)

def test_compute_mode_and_stats():
    # Create a mock distribution
    # 4 appears 5 times, 3 appears 2 times, 5 appears 1 time
    distribution = Counter({4: 5, 3: 2, 5: 1})
    
    stats = compute_mode_and_stats(distribution)
    
    assert stats["mode"] == 4
    assert stats["mode_count"] == 5
    assert stats["min"] == 3
    assert stats["max"] == 5
    assert stats["total_nodes"] == 8
    assert abs(stats["mean"] - 3.75) < 0.01

def test_validate_mode_for_amorphous_silicon_valid():
    # Valid mode for a-Si (typically 4)
    stats = {"mode": 4, "mean": 4.0, "min": 3, "max": 5}
    assert validate_mode_for_amorphous_silicon(stats) is True

def test_validate_mode_for_amorphous_silicon_invalid():
    # Invalid mode (e.g., 2 or 6)
    stats_low = {"mode": 2, "mean": 2.0, "min": 1, "max": 3}
    assert validate_mode_for_amorphous_silicon(stats_low) is False

    stats_high = {"mode": 6, "mean": 6.0, "min": 5, "max": 7}
    assert validate_mode_for_amorphous_silicon(stats_high) is False

def test_main_integration():
    # Create temporary directory and mock graph files
    with tempfile.TemporaryDirectory() as tmpdir:
        graph_dir = Path(tmpdir) / "graphs"
        graph_dir.mkdir()
        
        # Create a mock graph file
        mock_graph = {
            "nodes": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],
            "adj": {
                1: [2, 3, 4],
                2: [1, 3, 4],
                3: [1, 2, 4, 5],
                4: [1, 2, 3, 5],
                5: [3, 4]
            }
        }
        
        with open(graph_dir / "sample1.pkl", "wb") as f:
            import pickle
            pickle.dump(mock_graph, f)
        
        # Create output file path
        output_file = Path(tmpdir) / "stats.json"
        
        # Mock config and paths to use our temp dir
        import ingest.node_degree_stats_generator as module
        original_get_paths = module.get_paths
        
        def mock_get_paths():
            return {
                "graph_output": str(graph_dir),
                "node_degree_stats_output": str(output_file)
            }
        
        module.get_paths = mock_get_paths
        
        try:
            result = main()
            
            # Verify file exists
            assert output_file.exists()
            
            # Verify content
            with open(output_file, "r") as f:
                saved_stats = json.load(f)
            
            assert "mode" in saved_stats
            assert "validation_passed" in saved_stats
            assert saved_stats["validation_passed"] is True
            
            # Verify mode is 4 (most common in mock data)
            assert saved_stats["mode"] == 4
            
        finally:
            module.get_paths = original_get_paths