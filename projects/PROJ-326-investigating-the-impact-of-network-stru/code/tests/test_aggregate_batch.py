import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.generators.aggregate_batch import (
    load_batch_file,
    find_batch_files,
    aggregate_batches,
    generate_manifest,
    save_manifest,
    verify_threshold,
    main,
    BATCH_THRESHOLD
)

@pytest.fixture
def temp_batch_dir():
    """Create a temporary directory with mock batch files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create mock batch files
        batch1 = [
            {"id": "g1", "topology_class": "er", "clustering": 0.1},
            {"id": "g2", "topology_class": "er", "clustering": 0.15}
        ]
        batch2 = [
            {"id": "g3", "topology_class": "sw", "clustering": 0.4},
            {"id": "g4", "topology_class": "sw", "clustering": 0.45},
            {"id": "g5", "topology_class": "sf", "clustering": 0.2}
        ]
        
        with open(tmp_path / "batch_er.json", "w") as f:
            json.dump(batch1, f)
        with open(tmp_path / "batch_sw.json", "w") as f:
            json.dump(batch2, f)
        
        yield tmp_path

def test_load_batch_file_valid(temp_batch_dir):
    batch_path = temp_batch_dir / "batch_er.json"
    data = load_batch_file(batch_path)
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["id"] == "g1"

def test_load_batch_file_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            load_batch_file(Path(tmpdir) / "nonexistent.json")

def test_find_batch_files(temp_batch_dir):
    files = find_batch_files(temp_batch_dir)
    assert len(files) == 2
    names = [f.name for f in files]
    assert "batch_er.json" in names
    assert "batch_sw.json" in names

def test_aggregate_batches(temp_batch_dir):
    files = find_batch_files(temp_batch_dir)
    combined = aggregate_batches(files)
    assert len(combined) == 5
    # Check topology distribution
    classes = [g["topology_class"] for g in combined]
    assert classes.count("er") == 2
    assert classes.count("sw") == 2
    assert classes.count("sf") == 1

def test_generate_manifest(temp_batch_dir):
    files = find_batch_files(temp_batch_dir)
    combined = aggregate_batches(files)
    manifest = generate_manifest(combined, files)
    
    assert manifest["total_graphs"] == 5
    assert "generated_at" in manifest
    assert len(manifest["source_batches"]) == 2
    assert manifest["topology_distribution"]["er"] == 2
    assert manifest["threshold_required"] == BATCH_THRESHOLD

def test_verify_threshold_pass():
    manifest = {"total_graphs": 150, "threshold_required": 100}
    assert verify_threshold(manifest) is True

def test_verify_threshold_fail():
    manifest = {"total_graphs": 50, "threshold_required": 100}
    with pytest.raises(ValueError, match="Threshold verification FAILED"):
        verify_threshold(manifest)

def test_main_with_valid_batches(temp_batch_dir):
    output_file = temp_batch_dir / "manifest.json"
    args = [
        "--data-dir", str(temp_batch_dir),
        "--output", str(output_file)
    ]
    result = main(args)
    assert result == 0
    assert output_file.exists()
    
    with open(output_file) as f:
        manifest = json.load(f)
    assert manifest["total_graphs"] == 5
    assert manifest["threshold_met"] is False  # 5 < 100

def test_main_strict_mode_fail(temp_batch_dir):
    output_file = temp_batch_dir / "manifest_strict.json"
    args = [
        "--data-dir", str(temp_batch_dir),
        "--output", str(output_file),
        "--strict"
    ]
    # Should fail because 5 < 100
    with pytest.raises(ValueError):
        main(args)