"""
Tests for batch aggregation functionality.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.src.generators.aggregate_batch import (
    load_batch_file,
    find_batch_files,
    aggregate_batches,
    generate_manifest,
    verify_threshold,
    main
)

@pytest.fixture
def temp_batch_dir(tmp_path):
    """Create a temporary directory with mock batch files."""
    # Create batch files
    batch1_data = {
        "graphs": [
            {"id": "1", "topology_class": "erdos_renyi", "nodes": 10},
            {"id": "2", "topology_class": "erdos_renyi", "nodes": 10}
        ]
    }
    batch2_data = [
        {"id": "3", "topology_class": "watts_strogatz", "nodes": 10},
        {"id": "4", "topology_class": "watts_strogatz", "nodes": 10},
        {"id": "5", "topology_class": "barabasi_albert", "nodes": 10}
    ]
    
    batch1_path = tmp_path / "batch_erdos.json"
    batch2_path = tmp_path / "batch_watts.json"
    
    with open(batch1_path, 'w') as f:
        json.dump(batch1_data, f)
    
    with open(batch2_path, 'w') as f:
        json.dump(batch2_data, f)
    
    return tmp_path

def test_load_batch_file_valid(temp_batch_dir):
    """Test loading a valid batch file."""
    batch_path = temp_batch_dir / "batch_erdos.json"
    graphs = load_batch_file(batch_path)
    
    assert len(graphs) == 2
    assert graphs[0]["id"] == "1"
    assert graphs[0]["topology_class"] == "erdos_renyi"

def test_load_batch_file_missing(temp_batch_dir):
    """Test loading a non-existent batch file."""
    batch_path = temp_batch_dir / "nonexistent.json"
    graphs = load_batch_file(batch_path)
    
    assert graphs == []

def test_find_batch_files(temp_batch_dir):
    """Test finding batch files in a directory."""
    files = find_batch_files(temp_batch_dir)
    
    assert len(files) == 2
    filenames = [f.name for f in files]
    assert "batch_erdos.json" in filenames
    assert "batch_watts.json" in filenames

def test_aggregate_batches(temp_batch_dir):
    """Test aggregating multiple batch files."""
    files = find_batch_files(temp_batch_dir)
    all_graphs = aggregate_batches(files)
    
    assert len(all_graphs) == 5
    topology_classes = [g["topology_class"] for g in all_graphs]
    assert topology_classes.count("erdos_renyi") == 2
    assert topology_classes.count("watts_strogatz") == 2
    assert topology_classes.count("barabasi_albert") == 1

def test_generate_manifest(temp_batch_dir):
    """Test manifest generation."""
    files = find_batch_files(temp_batch_dir)
    all_graphs = aggregate_batches(files)
    
    output_path = temp_batch_dir / "manifest.json"
    manifest = generate_manifest(all_graphs, files, output_path)
    
    assert manifest["total_graphs"] == 5
    assert manifest["threshold_met"] == False  # 5 < 100
    assert manifest["threshold_required"] == 100
    assert "erdos_renyi" in manifest["topology_distribution"]
    assert manifest["validation_status"] == "failed"

def test_verify_threshold_pass():
    """Test threshold verification when passed."""
    manifest = {"total_graphs": 150, "threshold_required": 100}
    assert verify_threshold(manifest) == True

def test_verify_threshold_fail():
    """Test threshold verification when failed."""
    manifest = {"total_graphs": 50, "threshold_required": 100}
    assert verify_threshold(manifest) == False

def test_main_with_valid_batches(temp_batch_dir, capsys):
    """Test main function with valid batches."""
    # Create a manifest output path
    output_path = temp_batch_dir / "global_batch_manifest.json"
    
    # Mock arguments
    sys.argv = [
        "test_aggregate_batch.py",
        "--data-dir", str(temp_batch_dir),
        "--output", str(output_path)
    ]
    
    result = main()
    
    assert result == 0
    assert output_path.exists()
    
    with open(output_path, 'r') as f:
        manifest = json.load(f)
    
    assert manifest["total_graphs"] == 5
    assert manifest["validation_status"] == "failed"

def test_main_strict_mode_fail(temp_batch_dir):
    """Test main function in strict mode when threshold not met."""
    output_path = temp_batch_dir / "global_batch_manifest_strict.json"
    
    sys.argv = [
        "test_aggregate_batch.py",
        "--data-dir", str(temp_batch_dir),
        "--output", str(output_path),
        "--strict"
    ]
    
    with pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1