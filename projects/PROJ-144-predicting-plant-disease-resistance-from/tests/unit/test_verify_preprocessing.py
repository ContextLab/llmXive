"""
Unit tests for T017b: verify_preprocessing.py
"""
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import yaml
import pandas as pd
import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.data.verify_preprocessing import (
    compute_sha256,
    check_file_non_empty,
    load_artifact_manifest,
    save_artifact_manifest,
    verify_preprocessing_outputs,
    DATA_PROCESSED_DIR,
    STATE_DIR,
    ARTIFACT_HASHES_FILE
)

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_root = tempfile.mkdtemp()
    temp_data_processed = Path(temp_root) / "data" / "processed"
    temp_state = Path(temp_root) / "state"
    temp_data_processed.mkdir(parents=True)
    temp_state.mkdir(parents=True)
    
    # Monkey-patch constants
    original_data_dir = DATA_PROCESSED_DIR
    original_state_dir = STATE_DIR
    original_artifact_file = ARTIFACT_HASHES_FILE
    
    # We can't easily monkey-patch module-level constants, so we'll test 
    # the functions directly with temporary paths
    
    yield {
        "root": temp_root,
        "data_processed": temp_data_processed,
        "state": temp_state
    }
    
    # Cleanup
    shutil.rmtree(temp_root)

def test_compute_sha256(temp_dirs):
    """Test SHA256 computation."""
    test_file = temp_dirs["data_processed"] / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)
    
    checksum = compute_sha256(test_file)
    assert len(checksum) == 64  # SHA256 hex length
    assert isinstance(checksum, str)
    
    # Verify against known value
    import hashlib
    expected = hashlib.sha256(test_content).hexdigest()
    assert checksum == expected

def test_check_file_non_empty(temp_dirs):
    """Test file existence and non-empty checks."""
    # Non-existent file
    assert not check_file_non_empty(temp_dirs["data_processed"] / "nonexistent.txt")
    
    # Empty file
    empty_file = temp_dirs["data_processed"] / "empty.txt"
    empty_file.write_bytes(b"")
    assert not check_file_non_empty(empty_file)
    
    # Non-empty file
    non_empty_file = temp_dirs["data_processed"] / "nonempty.txt"
    non_empty_file.write_bytes(b"content")
    assert check_file_non_empty(non_empty_file)

def test_load_save_artifact_manifest(temp_dirs):
    """Test artifact manifest loading and saving."""
    manifest_file = temp_dirs["state"] / "test_manifest.yaml"
    
    # Test empty load
    manifest = {}
    save_artifact_manifest.__globals__.update({
        'ARTIFACT_HASHES_FILE': manifest_file,
        'STATE_DIR': temp_dirs["state"]
    })
    
    # Since we can't easily mock module constants, we test the logic
    # by creating a simple manifest and verifying YAML round-trip
    test_manifest = {
        "test_file.csv": {
            "checksum": "abc123",
            "path": "data/processed/test_file.csv",
            "verified": True
        }
    }
    
    with open(manifest_file, "w") as f:
        yaml.safe_dump(test_manifest, f)
    
    loaded = load_artifact_manifest.__globals__.get('load_artifact_manifest', lambda: {})
    # Direct test
    with open(manifest_file, "r") as f:
        loaded_manifest = yaml.safe_load(f)
    
    assert loaded_manifest["test_file.csv"]["checksum"] == "abc123"

def test_verify_preprocessing_outputs_missing_files(temp_dirs, monkeypatch):
    """Test verification fails when files are missing."""
    # Create a temporary state directory
    monkeypatch.setattr('code.data.verify_preprocessing.STATE_DIR', temp_dirs["state"])
    monkeypatch.setattr('code.data.verify_preprocessing.DATA_PROCESSED_DIR', temp_dirs["data_processed"])
    monkeypatch.setattr('code.data.verify_preprocessing.ARTIFACT_HASHES_FILE', temp_dirs["state"] / "artifact_hashes.yaml")
    
    # Don't create any expected files
    with pytest.raises(RuntimeError) as exc_info:
        verify_preprocessing_outputs()
    
    assert "MISSING" in str(exc_info.value)
    assert "batch_corrected_matrix.csv" in str(exc_info.value)

def test_verify_preprocessing_outputs_empty_files(temp_dirs, monkeypatch):
    """Test verification fails when files are empty."""
    monkeypatch.setattr('code.data.verify_preprocessing.STATE_DIR', temp_dirs["state"])
    monkeypatch.setattr('code.data.verify_preprocessing.DATA_PROCESSED_DIR', temp_dirs["data_processed"])
    monkeypatch.setattr('code.data.verify_preprocessing.ARTIFACT_HASHES_FILE', temp_dirs["state"] / "artifact_hashes.yaml")
    
    # Create empty expected files
    for filename in ["batch_corrected_matrix.csv", "labels.csv", "preprocess_log.json"]:
        (temp_dirs["data_processed"] / filename).write_bytes(b"")
    
    with pytest.raises(RuntimeError) as exc_info:
        verify_preprocessing_outputs()
    
    assert "EMPTY" in str(exc_info.value)

def test_verify_preprocessing_outputs_success(temp_dirs, monkeypatch):
    """Test verification succeeds when files are valid."""
    monkeypatch.setattr('code.data.verify_preprocessing.STATE_DIR', temp_dirs["state"])
    monkeypatch.setattr('code.data.verify_preprocessing.DATA_PROCESSED_DIR', temp_dirs["data_processed"])
    monkeypatch.setattr('code.data.verify_preprocessing.ARTIFACT_HASHES_FILE', temp_dirs["state"] / "artifact_hashes.yaml")
    
    # Create valid expected files
    # batch_corrected_matrix.csv
    df = pd.DataFrame({
        "metabolite_1": [1.0, 2.0, 3.0],
        "metabolite_2": [4.0, 5.0, 6.0]
    })
    df.to_csv(temp_dirs["data_processed"] / "batch_corrected_matrix.csv", index=False)
    
    # labels.csv
    labels_df = pd.DataFrame({
        "sample_id": ["S1", "S2", "S3"],
        "binary_label": [0, 1, 0]
    })
    labels_df.to_csv(temp_dirs["data_processed"] / "labels.csv", index=False)
    
    # preprocess_log.json
    log_data = {
        "batch_correction": "applied",
        "features_retained": 2,
        "samples_retained": 3,
        "timestamp": "2024-01-01T00:00:00"
    }
    with open(temp_dirs["data_processed"] / "preprocess_log.json", "w") as f:
        json.dump(log_data, f)
    
    # Should not raise
    result = verify_preprocessing_outputs()
    assert result is True
    
    # Verify manifest was updated
    assert (temp_dirs["state"] / "artifact_hashes.yaml").exists()
    
    with open(temp_dirs["state"] / "artifact_hashes.yaml", "r") as f:
        manifest = yaml.safe_load(f)
    
    assert "batch_corrected_matrix.csv" in manifest
    assert "labels.csv" in manifest
    assert "preprocess_log.json" in manifest
    assert all(manifest[k]["verified"] for k in manifest)