import json
import os
import pickle
import pytest
from pathlib import Path
import tempfile
import shutil

from analysis.graph_checksum_generator import (
    calculate_file_checksum,
    find_graph_files,
    generate_checksums_for_graphs,
    save_checksum_manifest,
    main
)
from config import get_config, get_paths

@pytest.fixture
def temp_graph_dir():
    """Create a temporary directory with mock graph files."""
    temp_dir = tempfile.mkdtemp()
    graph_dir = Path(temp_dir)
    
    # Create mock graph files
    for i in range(3):
        mock_graph = {
            "nodes": [{"id": j, "coords": [0.0, 0.0, 0.0], "degree": 4, "clustering_coeff": 0.5} for j in range(10)],
            "edges": [[i, i+1] for i in range(9)]
        }
        file_path = graph_dir / f"graph_sample_{i}.pkl"
        with open(file_path, 'wb') as f:
            pickle.dump(mock_graph, f)
    
    yield graph_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_calculate_file_checksum(temp_graph_dir):
    """Test checksum calculation for a single file."""
    file_path = temp_graph_dir / "graph_sample_0.pkl"
    checksum = calculate_file_checksum(file_path)
    
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)

def test_find_graph_files(temp_graph_dir):
    """Test finding graph files in a directory."""
    files = find_graph_files(temp_graph_dir)
    
    assert len(files) == 3
    assert all(f.name.startswith("graph_sample_") for f in files)

def test_generate_checksums_for_graphs(temp_graph_dir):
    """Test generating checksums for multiple files."""
    files = find_graph_files(temp_graph_dir)
    checksums = generate_checksums_for_graphs(files)
    
    assert len(checksums) == 3
    assert all(len(v) == 64 for v in checksums.values())

def test_save_checksum_manifest(temp_graph_dir):
    """Test saving checksum manifest to JSON."""
    files = find_graph_files(temp_graph_dir)
    checksums = generate_checksums_for_graphs(files)
    
    output_path = temp_graph_dir / "test_checksums.json"
    save_checksum_manifest(checksums, output_path)
    
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        manifest = json.load(f)
    
    assert "checksums" in manifest
    assert "algorithm" in manifest
    assert manifest["algorithm"] == "sha256"
    assert len(manifest["checksums"]) == 3

def test_main_integration(temp_graph_dir, mocker):
    """Test the main function integration."""
    # Mock config and paths to use temp directory
    mock_paths = {
        'processed_graphs': str(temp_graph_dir),
        'checksums_file': str(temp_graph_dir / "generated_checksums.json")
    }
    
    mocker.patch('analysis.graph_checksum_generator.get_paths', return_value=mock_paths)
    mocker.patch('analysis.graph_checksum_generator.get_config', return_value={})
    
    main()
    
    output_file = Path(mock_paths['checksums_file'])
    assert output_file.exists()
    
    with open(output_file, 'r') as f:
        manifest = json.load(f)
    
    assert len(manifest["checksums"]) == 3