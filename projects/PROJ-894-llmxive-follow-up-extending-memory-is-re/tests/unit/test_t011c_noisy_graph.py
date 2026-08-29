"""
Unit tests for T011c: Generate Noisy Graph Dataset
"""
import pytest
import json
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from data_loader import generate_noisy_graph_dataset, load_config
from graph_utils import inject_noise

@pytest.fixture
def sample_clean_graphs():
    """Create a sample clean graphs dictionary for testing."""
    return {
        "task_1": {
            "nodes": ["A", "B", "C", "D"],
            "edges": [
                {"source": "A", "target": "B", "relation": "rel1"},
                {"source": "B", "target": "C", "relation": "rel2"},
                {"source": "C", "target": "D", "relation": "rel3"}
            ]
        },
        "task_2": {
            "nodes": ["X", "Y", "Z"],
            "edges": [
                {"source": "X", "target": "Y", "relation": "relA"},
                {"source": "Y", "target": "Z", "relation": "relB"}
            ]
        }
    }

@pytest.fixture
def temp_graph_files(sample_clean_graphs):
    """Create temporary files for clean and noisy graphs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        clean_path = os.path.join(tmpdir, "graphs_raw.json")
        noisy_path = os.path.join(tmpdir, "graph_noise_42.json")
        
        # Write clean graphs
        with open(clean_path, 'w') as f:
            json.dump(sample_clean_graphs, f)
        
        yield clean_path, noisy_path

def test_noisy_graph_generation(temp_graph_files):
    """Test that noisy graph generation creates valid output."""
    clean_path, noisy_path = temp_graph_files
    
    # Create minimal config
    config = {
        "noise": {"injection_ratio": 0.1, "seed": 42},
        "paths": {
            "clean_graphs": clean_path,
            "noisy_graphs": noisy_path
        }
    }
    
    # Generate noisy graphs
    output_path = generate_noisy_graph_dataset(config)
    
    # Verify output file exists and is non-empty
    assert os.path.exists(output_path), f"Output file not created: {output_path}"
    assert os.path.getsize(output_path) > 0, "Output file is empty"
    
    # Verify content structure
    with open(output_path, 'r') as f:
        noisy_graphs = json.load(f)
    
    assert len(noisy_graphs) == 2, "Wrong number of graphs generated"
    assert "task_1" in noisy_graphs, "task_1 missing from output"
    assert "task_2" in noisy_graphs, "task_2 missing from output"

def test_edge_count_preservation(temp_graph_files):
    """Test that noisy graph generation preserves edge counts."""
    clean_path, noisy_path = temp_graph_files
    
    config = {
        "noise": {"injection_ratio": 0.1, "seed": 42},
        "paths": {
            "clean_graphs": clean_path,
            "noisy_graphs": noisy_path
        }
    }
    
    # Load original graphs
    with open(clean_path, 'r') as f:
        clean_graphs = json.load(f)
    
    # Generate noisy graphs
    generate_noisy_graph_dataset(config)
    
    # Load noisy graphs
    with open(noisy_path, 'r') as f:
        noisy_graphs = json.load(f)
    
    # Verify edge counts match
    for task_id in clean_graphs:
        original_edges = len(clean_graphs[task_id]['edges'])
        noisy_edges = len(noisy_graphs[task_id]['edges'])
        assert original_edges == noisy_edges, \
            f"Edge count mismatch for {task_id}: {original_edges} vs {noisy_edges}"

def test_deterministic_noise_generation(temp_graph_files):
    """Test that noise generation is deterministic with same seed."""
    clean_path, noisy_path = temp_graph_files
    
    config = {
        "noise": {"injection_ratio": 0.1, "seed": 42},
        "paths": {
            "clean_graphs": clean_path,
            "noisy_graphs": noisy_path
        }
    }
    
    # Generate twice
    generate_noisy_graph_dataset(config)
    with open(noisy_path, 'r') as f:
        first_run = f.read()
    
    generate_noisy_graph_dataset(config)
    with open(noisy_path, 'r') as f:
        second_run = f.read()
    
    assert first_run == second_run, "Noise generation is not deterministic"

def test_missing_clean_graphs_raises_error():
    """Test that missing clean graphs file raises appropriate error."""
    config = {
        "noise": {"injection_ratio": 0.1, "seed": 42},
        "paths": {
            "clean_graphs": "/nonexistent/path/graphs.json",
            "noisy_graphs": "/tmp/noisy.json"
        }
    }
    
    with pytest.raises(FileNotFoundError):
        generate_noisy_graph_dataset(config)

def test_empty_clean_graphs_raises_error(temp_graph_files):
    """Test that empty clean graphs file raises appropriate error."""
    clean_path, noisy_path = temp_graph_files
    
    # Overwrite with empty file
    with open(clean_path, 'w') as f:
        f.write("{}")
    
    config = {
        "noise": {"injection_ratio": 0.1, "seed": 42},
        "paths": {
            "clean_graphs": clean_path,
            "noisy_graphs": noisy_path
        }
    }
    
    # Should raise ValueError for empty graphs
    with pytest.raises(ValueError):
        generate_noisy_graph_dataset(config)