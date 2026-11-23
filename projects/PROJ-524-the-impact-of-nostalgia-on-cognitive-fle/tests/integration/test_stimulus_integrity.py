"""
Integration test for Task T015: Stimulus Integrity
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

from task_t015_stimulus_integrity import (
    fetch_canonical_checksum_from_metadata,
    compute_local_checksum,
    check_integrity,
    save_report
)
from config import get_config

def compute_sha256_file(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

@pytest.fixture
def temp_stimuli_env():
    """Creates a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        
        # Create stimuli directory
        stimuli_dir = tmp_path / "data" / "stimuli"
        stimuli_dir.mkdir(parents=True)
        
        # Create a dummy stimulus file
        dummy_file = stimuli_dir / "stimulus_a.txt"
        dummy_content = b"This is a test stimulus file."
        dummy_file.write_bytes(dummy_content)
        
        # Create metadata
        metadata_dir = tmp_path / "data" / "raw"
        metadata_dir.mkdir(parents=True)
        metadata_file = metadata_dir / "metadata.json"
        
        correct_hash = compute_sha256_file(dummy_file)
        
        metadata = {
            "dataset_source": "test_source",
            "stimuli_checksums": {
                "stimulus_a.txt": correct_hash,
                "missing_file.txt": "0000000000000000000000000000000000000000000000000000000000000000"
            }
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f)
        
        yield {
            "base": tmp_path,
            "stimuli_dir": stimuli_dir,
            "metadata_file": metadata_file,
            "dummy_file": dummy_file,
            "correct_hash": correct_hash
        }

def test_check_integrity_pass(temp_stimuli_env):
    """Test that integrity check passes when all files match."""
    # Modify metadata to remove the missing file for this specific test
    metadata_file = temp_stimuli_env["metadata_file"]
    with open(metadata_file, 'r') as f:
        meta = json.load(f)
    
    # Only include the file that exists
    meta["stimuli_checksums"] = {
        "stimulus_a.txt": temp_stimuli_env["correct_hash"]
    }
    
    with open(metadata_file, 'w') as f:
        json.dump(meta, f)
    
    expected = fetch_canonical_checksum_from_metadata(metadata_file)
    success, report = check_integrity(
        temp_stimuli_env["stimuli_dir"], 
        expected, 
        simulation_mode=False
    )
    
    assert success is True
    assert report["status"] == "PASSED"
    assert len(report["errors"]) == 0

def test_check_integrity_missing_file(temp_stimuli_env):
    """Test that integrity check fails when a file is missing."""
    expected = fetch_canonical_checksum_from_metadata(temp_stimuli_env["metadata_file"])
    
    success, report = check_integrity(
        temp_stimuli_env["stimuli_dir"],
        expected,
        simulation_mode=False
    )
    
    assert success is False
    assert report["status"] == "FAILED_MISSING"
    assert any(e["type"] == "ERR_STIMULUS_MISSING" for e in report["errors"])

def test_check_integrity_corrupt_file(temp_stimuli_env):
    """Test that integrity check fails when a file is corrupted (hash mismatch)."""
    # Corrupt the file
    temp_stimuli_env["dummy_file"].write_bytes(b"Corrupted content")
    
    expected = fetch_canonical_checksum_from_metadata(temp_stimuli_env["metadata_file"])
    
    success, report = check_integrity(
        temp_stimuli_env["stimuli_dir"],
        expected,
        simulation_mode=False
    )
    
    assert success is False
    assert report["status"] == "FAILED_CORRUPT"
    assert any(e["type"] == "ERR_STIMULUS_CORRUPT" for e in report["errors"])

def test_check_integrity_simulation_mode(temp_stimuli_env):
    """Test that integrity check is skipped in simulation mode."""
    expected = fetch_canonical_checksum_from_metadata(temp_stimuli_env["metadata_file"])
    
    success, report = check_integrity(
        temp_stimuli_env["stimuli_dir"],
        expected,
        simulation_mode=True
    )
    
    assert success is True
    assert report["status"] == "SKIPPED_SIMULATION"
    assert "SKIPPED_STIMULUS_CHECK_SIMULATION" in report["checks_performed"]

def test_compute_local_checksum(temp_stimuli_env):
    """Test checksum computation."""
    computed = compute_local_checksum(temp_stimuli_env["dummy_file"])
    assert computed == temp_stimuli_env["correct_hash"]
    
    # Verify mismatch
    temp_stimuli_env["dummy_file"].write_bytes(b"Changed")
    computed_new = compute_local_checksum(temp_stimuli_env["dummy_file"])
    assert computed_new != temp_stimuli_env["correct_hash"]
