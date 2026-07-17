import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Ensure imports work from project root
if "code" not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from code.src.generators.aggregate_batch import (
    find_batch_files,
    load_batch_file,
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
        batch_er = [
            {"id": "er_1", "topology_class": "ErdosRenyi", "nodes": 10},
            {"id": "er_2", "topology_class": "ErdosRenyi", "nodes": 10}
        ]
        batch_sw = [
            {"id": "sw_1", "topology_class": "WattsStrogatz", "nodes": 10},
            {"id": "sw_2", "topology_class": "WattsStrogatz", "nodes": 10},
            {"id": "sw_3", "topology_class": "WattsStrogatz", "nodes": 10}
        ]
        batch_sf = [
            {"id": "sf_1", "topology_class": "BarabasiAlbert", "nodes": 10}
        ]
        
        with open(tmp_path / "batch_ErdosRenyi.json", "w") as f:
            json.dump(batch_er, f)
        with open(tmp_path / "batch_WattsStrogatz.json", "w") as f:
            json.dump(batch_sw, f)
        with open(tmp_path / "batch_BarabasiAlbert.json", "w") as f:
            json.dump(batch_sf, f)
        
        yield tmp_path

def test_find_batch_files(temp_batch_dir):
    files = find_batch_files(temp_batch_dir)
    assert len(files) == 3
    assert all(f.name.startswith("batch_") and f.name.endswith(".json") for f in files)

def test_load_batch_file_valid(temp_batch_dir):
    file_path = temp_batch_dir / "batch_ErdosRenyi.json"
    data = load_batch_file(file_path)
    assert isinstance(data, list)
    assert len(data) == 2

def test_load_batch_file_missing(temp_batch_dir):
    file_path = temp_batch_dir / "batch_NonExistent.json"
    with pytest.raises(FileNotFoundError):
        load_batch_file(file_path)

def test_aggregate_batches(temp_batch_dir):
    batch_files = find_batch_files(temp_batch_dir)
    combined = aggregate_batches(batch_files)
    assert len(combined) == 6  # 2 + 3 + 1

def test_generate_manifest(temp_batch_dir):
    batch_files = find_batch_files(temp_batch_dir)
    combined = aggregate_batches(batch_files)
    manifest = generate_manifest(combined, batch_files)
    
    assert manifest["total_graphs"] == 6
    assert "ErdosRenyi" in manifest["topology_distribution"]
    assert manifest["topology_distribution"]["ErdosRenyi"] == 2
    assert manifest["threshold_required"] == BATCH_THRESHOLD
    assert manifest["threshold_met"] == False  # 6 < 100

def test_verify_threshold_pass():
    manifest = {"total_graphs": 150, "threshold_required": 100}
    assert verify_threshold(manifest) is True

def test_verify_threshold_fail():
    manifest = {"total_graphs": 50, "threshold_required": 100}
    with pytest.raises(ValueError, match="Threshold verification FAILED"):
        verify_threshold(manifest)

def test_main_with_valid_batches(temp_batch_dir):
    output_file = temp_batch_dir / "global_batch_manifest.json"
    ret = main(["--data-dir", str(temp_batch_dir), "--output", str(output_file), "--strict"])
    assert ret == 0
    assert output_file.exists()
    
    with open(output_file) as f:
        manifest = json.load(f)
    assert manifest["total_graphs"] == 6

def test_main_strict_mode_fail(temp_batch_dir):
    """Test that strict mode fails when threshold is not met."""
    output_file = temp_batch_dir / "global_batch_manifest.json"
    # This should raise an error because 6 < 100 and strict=True
    with pytest.raises(ValueError):
        main(["--data-dir", str(temp_batch_dir), "--output", str(output_file), "--strict"])
