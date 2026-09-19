"""
Unit tests for T015: Stimulus Integrity
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest
import yaml

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from task_t015_stimulus_integrity import (
    fetch_canonical_checksum_from_metadata,
    compute_local_checksum,
    generate_synthetic_stimuli,
    check_integrity,
    update_metadata_with_checksums,
    save_metadata,
    update_state_yaml,
    main
)
from utils import compute_sha256

@pytest.fixture
def temp_stimuli_dir():
    """Create a temporary stimuli directory."""
    temp_dir = tempfile.mkdtemp()
    stimuli_path = Path(temp_dir) / "stimuli"
    stimuli_path.mkdir()
    yield stimuli_path
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_metadata_file():
    """Create a temporary metadata file."""
    temp_dir = tempfile.mkdtemp()
    metadata_path = Path(temp_dir) / "metadata.json"
    metadata = {
        "dataset_source": "test_source",
        "simulation_mode": False,
        "stimuli_checksums": {}
    }
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f)
    yield metadata_path
    shutil.rmtree(temp_dir)

def test_compute_local_checksum(temp_stimuli_dir):
    """Test checksum computation for a file."""
    test_file = temp_stimuli_dir / "test.txt"
    test_content = "test content"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    checksum = compute_local_checksum(test_file)
    assert len(checksum) == 64  # SHA-256 hex length
    assert isinstance(checksum, str)

def test_fetch_canonical_checksum_from_metadata():
    """Test fetching checksums from metadata."""
    metadata_with_checksums = {
        "stimuli_checksums": {"file1.txt": "abc123", "file2.txt": "def456"}
    }
    metadata_without_checksums = {"dataset_source": "test"}
    
    result_with = fetch_canonical_checksum_from_metadata(metadata_with_checksums)
    assert result_with == {"file1.txt": "abc123", "file2.txt": "def456"}
    
    result_without = fetch_canonical_checksum_from_metadata(metadata_without_checksums)
    assert result_without is None

def test_generate_synthetic_stimuli(temp_stimuli_dir):
    """Test synthetic stimulus generation."""
    checksums = generate_synthetic_stimuli(temp_stimuli_dir)
    
    assert len(checksums) > 0
    assert "nostalgia_prompt.txt" in checksums
    assert "control_prompt.txt" in checksums
    
    # Verify files were created
    for filename in checksums.keys():
        assert (temp_stimuli_dir / filename).exists()

def test_check_integrity_success(temp_stimuli_dir):
    """Test integrity check with valid files."""
    # Create a test file
    test_file = temp_stimuli_dir / "test.txt"
    test_content = "test content"
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    expected_checksums = {"test.txt": compute_sha256(test_file)}
    is_valid, errors = check_integrity(temp_stimuli_dir, expected_checksums)
    
    assert is_valid is True
    assert len(errors) == 0

def test_check_integrity_missing_file(temp_stimuli_dir):
    """Test integrity check with missing file."""
    expected_checksums = {"missing.txt": "abc123"}
    is_valid, errors = check_integrity(temp_stimuli_dir, expected_checksums)
    
    assert is_valid is False
    assert len(errors) == 1
    assert "ERR_STIMULUS_MISSING" in errors[0]

def test_check_integrity_corrupt_file(temp_stimuli_dir):
    """Test integrity check with corrupted file."""
    test_file = temp_stimuli_dir / "test.txt"
    with open(test_file, 'w') as f:
        f.write("test content")
    
    expected_checksums = {"test.txt": "wrong_checksum"}
    is_valid, errors = check_integrity(temp_stimuli_dir, expected_checksums)
    
    assert is_valid is False
    assert len(errors) == 1
    assert "ERR_STIMULUS_CORRUPT" in errors[0]

def test_update_metadata_with_checksums():
    """Test metadata update with checksums."""
    metadata = {"dataset_source": "test"}
    checksums = {"file1.txt": "abc123"}
    
    updated = update_metadata_with_checksums(metadata, checksums)
    
    assert "stimuli_checksums" in updated
    assert updated["stimuli_checksums"] == checksums
    assert "timestamp" in updated

def test_save_metadata(temp_metadata_file):
    """Test metadata saving."""
    metadata = {"dataset_source": "test", "stimuli_checksums": {"file.txt": "abc123"}}
    save_metadata(metadata, temp_metadata_file)
    
    with open(temp_metadata_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded["dataset_source"] == "test"
    assert loaded["stimuli_checksums"] == {"file.txt": "abc123"}

def test_update_state_yaml(temp_metadata_file):
    """Test state YAML update."""
    temp_state = Path(temp_metadata_file.parent) / "state.yaml"
    checksums = {"file.txt": "abc123"}
    
    update_state_yaml(temp_state, checksums)
    
    assert temp_state.exists()
    with open(temp_state, 'r') as f:
        state_data = yaml.safe_load(f)
    
    assert "artifact_hashes" in state_data
    assert "stimuli" in state_data["artifact_hashes"]
    assert state_data["artifact_hashes"]["stimuli"] == checksums
