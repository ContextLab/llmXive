"""
Unit tests for T016c: Checksum Verification.
"""
import json
import os
import tempfile
import yaml
from pathlib import Path
import pytest

from utils.checksums import (
    compute_file_sha256,
    compute_string_sha256,
    verify_file_checksum,
    store_checksum_in_state,
    check_code_drift
)

@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        f_path = f.name
    yield f_path
    os.unlink(f_path)

@pytest.fixture
def temp_state_file():
    """Create a temporary state file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
        f_path = f.name
    yield f_path
    if os.path.exists(f_path):
        os.unlink(f_path)

def test_compute_file_sha256(temp_file):
    checksum1 = compute_file_sha256(temp_file)
    checksum2 = compute_file_sha256(temp_file)
    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA256 hex length

def test_compute_string_sha256():
    s = "test string"
    checksum = compute_string_sha256(s)
    assert len(checksum) == 64

def test_verify_file_checksum_success(temp_file):
    checksum = compute_file_sha256(temp_file)
    assert verify_file_checksum(temp_file, checksum) is True

def test_verify_file_checksum_failure(temp_file):
    checksum = compute_file_sha256(temp_file)
    assert verify_file_checksum(temp_file, "wrong_checksum") is False

def test_store_checksum_in_state(temp_file, temp_state_file):
    project_id = "test-project"
    store_checksum_in_state(project_id, temp_file, temp_state_file)
    
    assert os.path.exists(temp_state_file)
    with open(temp_state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert 'projects' in state
    assert project_id in state['projects']
    assert 'artifact_hashes' in state['projects'][project_id]
    assert temp_file in state['projects'][project_id]['artifact_hashes']

def test_check_code_drift_no_reference(temp_file):
    # Should return True if no reference is provided
    assert check_code_drift(temp_file) is True

def test_check_code_drift_match(temp_file):
    checksum = compute_file_sha256(temp_file)
    assert check_code_drift(temp_file, checksum) is True

def test_check_code_drift_mismatch(temp_file):
    assert check_code_drift(temp_file, "wrong_checksum") is False
