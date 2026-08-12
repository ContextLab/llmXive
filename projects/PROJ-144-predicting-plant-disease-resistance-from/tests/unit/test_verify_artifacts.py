"""
Unit tests for T033 artifact verification logic.
"""
import os
import json
import tempfile
import yaml
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from utils.verify_artifacts import (
    load_artifact_hashes,
    verify_artifact_exists,
    verify_hash_in_registry,
    EXPECTED_ARTIFACTS
)
from utils.io import compute_file_hash

@pytest.fixture
def temp_state_dir(tmp_path):
    """Create a temporary state directory for testing."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    return state_dir

@pytest.fixture
def temp_artifact_dir(tmp_path):
    """Create a temporary directory with mock artifacts."""
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    
    # Create mock files
    (data_dir / "batch_corrected_matrix.csv").write_text("col1,col2\n1,2\n3,4")
    (data_dir / "labels.csv").write_text("id,label\n1,0\n2,1")
    
    return tmp_path

def test_load_artifact_hashes_empty(temp_state_dir):
    """Test loading from non-existent file returns empty dict."""
    result = load_artifact_hashes()
    assert result == {}

def test_load_artifact_hashes_valid(temp_state_dir):
    """Test loading from existing yaml file."""
    hash_file = temp_state_dir / "artifact_hashes.yaml"
    test_data = {"/path/to/file.csv": "abc123"}
    with open(hash_file, 'w') as f:
        yaml.dump(test_data, f)
    
    result = load_artifact_hashes()
    assert result == test_data

def test_verify_artifact_exists_true(temp_artifact_dir):
    """Test verification of existing file."""
    path = str(temp_artifact_dir / "data" / "processed" / "batch_corrected_matrix.csv")
    exists, msg = verify_artifact_exists(path)
    assert exists is True
    assert msg == "OK"

def test_verify_artifact_exists_false(temp_artifact_dir):
    """Test verification of missing file."""
    path = str(temp_artifact_dir / "data" / "processed" / "nonexistent.csv")
    exists, msg = verify_artifact_exists(path)
    assert exists is False
    assert "File missing" in msg

def test_verify_hash_in_registry_present():
    """Test verification when hash is in registry."""
    registry = {"/path/to/file.csv": "hash123"}
    exists, msg = verify_hash_in_registry("/path/to/file.csv", registry)
    assert exists is True
    assert msg == "Registered"

def test_verify_hash_in_registry_missing():
    """Test verification when hash is missing from registry."""
    registry = {}
    exists, msg = verify_hash_in_registry("/path/to/file.csv", registry)
    assert exists is False
    assert "Not registered" in msg

def test_expected_artifacts_list_not_empty():
    """Ensure EXPECTED_ARTIFACTS is populated."""
    assert len(EXPECTED_ARTIFACTS) > 0

def test_hash_computation_consistency(temp_artifact_dir):
    """Test that hash computation is deterministic."""
    path = str(temp_artifact_dir / "data" / "processed" / "batch_corrected_matrix.csv")
    hash1 = compute_file_hash(path)
    hash2 = compute_file_hash(path)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length
