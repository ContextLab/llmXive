import os
import json
import tempfile
import pytest
from pathlib import Path
import hashlib
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from src.integrity import (
    compute_file_hash,
    generate_hashes,
    save_hashes,
    load_hashes,
    verify_integrity,
    update_hashes,
    IntegrityError,
    get_state_path
)
from src.utils import get_logger

@pytest.fixture
def temp_dirs():
    """Creates a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir) / "data"
        state_dir = Path(tmpdir) / "state" / "projects"
        data_dir.mkdir()
        state_dir.mkdir(parents=True)
        yield {
            "data": data_dir,
            "state": state_dir,
            "tmp": Path(tmpdir)
        }

@pytest.fixture
def sample_files(temp_dirs):
    """Creates sample files in the data directory."""
    data_dir = temp_dirs["data"]
    
    # Create a text file
    file1 = data_dir / "test.txt"
    file1.write_text("Hello, World!")
    
    # Create a JSON file
    file2 = data_dir / "config.json"
    file2.write_text('{"key": "value"}')
    
    # Create a nested file
    nested = data_dir / "subdir"
    nested.mkdir()
    file3 = nested / "data.nii.gz"
    file3.write_bytes(b"fake_nifti_data")
    
    return [file1, file2, file3]

def test_compute_file_hash_sample_files(sample_files):
    """Test that compute_file_hash returns correct SHA-256 for known content."""
    file1 = sample_files[0]
    expected_hash = hashlib.sha256(b"Hello, World!").hexdigest()
    actual_hash = compute_file_hash(file1)
    assert actual_hash == expected_hash

def test_compute_file_hash_nonexistent(temp_dirs):
    """Test that compute_file_hash raises FileNotFoundError for missing file."""
    missing_file = temp_dirs["data"] / "does_not_exist.txt"
    with pytest.raises(FileNotFoundError):
        compute_file_hash(missing_file)

def test_generate_hashes(temp_dirs, sample_files):
    """Test that generate_hashes finds all files and computes hashes."""
    hashes = generate_hashes(temp_dirs["data"])
    
    # Check count (3 files)
    assert len(hashes) == 3
    
    # Check keys are relative paths
    assert any("test.txt" in k for k in hashes.keys())
    assert any("config.json" in k for k in hashes.keys())
    assert any("data.nii.gz" in k for k in hashes.keys())
    
    # Check values are valid hex strings
    for h in hashes.values():
        assert len(h) == 64  # SHA-256 hex length

def test_save_and_load_hashes(temp_dirs, sample_files):
    """Test saving and loading hashes to/from state file."""
    state_file = temp_dirs["state"] / "test.yaml"
    hashes = generate_hashes(temp_dirs["data"])
    
    save_hashes(hashes, state_file)
    
    assert state_file.exists()
    
    loaded = load_hashes(state_file)
    assert loaded == hashes

def test_load_hashes_no_file(temp_dirs):
    """Test loading from a non-existent state file returns empty dict."""
    fake_path = temp_dirs["state"] / "non_existent.yaml"
    loaded = load_hashes(fake_path)
    assert loaded == {}

def test_verify_integrity_match(temp_dirs, sample_files):
    """Test verify_integrity passes when hashes match."""
    state_file = temp_dirs["state"] / "test.yaml"
    hashes = generate_hashes(temp_dirs["data"])
    save_hashes(hashes, state_file)
    
    # Should not raise
    assert verify_integrity(temp_dirs["data"], state_file) is True

def test_verify_integrity_mismatch(temp_dirs, sample_files):
    """Test verify_integrity raises when file content changes."""
    state_file = temp_dirs["state"] / "test.yaml"
    hashes = generate_hashes(temp_dirs["data"])
    save_hashes(hashes, state_file)
    
    # Modify a file
    file1 = sample_files[0]
    file1.write_text("Modified content")
    
    with pytest.raises(IntegrityError, match="Hash mismatch"):
        verify_integrity(temp_dirs["data"], state_file)

def test_verify_integrity_missing_file(temp_dirs, sample_files):
    """Test verify_integrity raises when a tracked file is deleted."""
    state_file = temp_dirs["state"] / "test.yaml"
    hashes = generate_hashes(temp_dirs["data"])
    save_hashes(hashes, state_file)
    
    # Delete a file
    file1 = sample_files[0]
    file1.unlink()
    
    with pytest.raises(IntegrityError, match="Missing artifact"):
        verify_integrity(temp_dirs["data"], state_file)

def test_update_hashes(temp_dirs, sample_files):
    """Test the update_hashes workflow."""
    state_file = temp_dirs["state"] / "test.yaml"
    
    # Initial update
    hashes = update_hashes(temp_dirs["data"], state_file)
    assert len(hashes) == 3
    
    # Modify file
    sample_files[0].write_text("New content")
    
    # Update again
    new_hashes = update_hashes(temp_dirs["data"], state_file)
    assert new_hashes[str(sample_files[0].relative_to(temp_dirs["data"]))] != hashes[str(sample_files[0].relative_to(temp_dirs["data"]))]
    assert len(new_hashes) == 3