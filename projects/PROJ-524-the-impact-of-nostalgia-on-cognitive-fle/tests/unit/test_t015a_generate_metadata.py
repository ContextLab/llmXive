"""
Unit tests for Task T015a: Generate Metadata.
"""
import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

# We will mock the config and utils imports if needed, but for now assume they exist
# In a real environment, these would be imported from the project
# For this test, we assume the functions are importable from the module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from task_t015a_generate_metadata import (
    compute_file_checksum,
    compute_stimuli_checksums,
    generate_metadata,
    save_metadata
)

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_compute_file_checksum(temp_dir):
    """Test SHA-256 checksum computation."""
    test_file = temp_dir / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_file_checksum(test_file)
    
    assert actual_hash == expected_hash

def test_compute_stimuli_checksums_empty_dir(temp_dir):
    """Test checksums on empty directory."""
    checksums = compute_stimuli_checksums(temp_dir)
    assert checksums == {}

def test_compute_stimuli_checksums_with_files(temp_dir):
    """Test checksums with multiple files."""
    file1 = temp_dir / "stim1.txt"
    file2 = temp_dir / "stim2.txt"
    
    file1.write_bytes(b"content1")
    file2.write_bytes(b"content2")
    
    checksums = compute_stimuli_checksums(temp_dir)
    
    assert "stim1.txt" in checksums
    assert "stim2.txt" in checksums
    assert checksums["stim1.txt"] == hashlib.sha256(b"content1").hexdigest()
    assert checksums["stim2.txt"] == hashlib.sha256(b"content2").hexdigest()

def test_generate_metadata_simulation_mode(temp_dir):
    """Test metadata generation in simulation mode."""
    stimuli_dir = temp_dir / "stimuli"
    stimuli_dir.mkdir()
    (stimuli_dir / "test.txt").write_bytes(b"test")
    
    metadata = generate_metadata(stimuli_dir, temp_dir / "metadata.json", simulation_mode=True)
    
    assert metadata["dataset_source"] == "simulated"
    assert metadata["simulation_mode"] is True
    assert "stimuli_checksums" in metadata
    assert "test.txt" in metadata["stimuli_checksums"]

def test_generate_metadata_real_mode(temp_dir):
    """Test metadata generation in real mode with existing metadata."""
    stimuli_dir = temp_dir / "stimuli"
    stimuli_dir.mkdir()
    (stimuli_dir / "test.txt").write_bytes(b"test")
    
    # Create a dummy raw metadata file to simulate existing data
    raw_meta_path = temp_dir / "raw_metadata.json"
    raw_meta_path.write_text(json.dumps({
        "dataset_source": "OpenML-12345",
        "validation_study_doi": "10.1038/some-doi"
    }))
    
    metadata = generate_metadata(stimuli_dir, raw_meta_path, simulation_mode=False)
    
    assert metadata["dataset_source"] == "OpenML-12345"
    assert metadata["validation_study_doi"] == "10.1038/some-doi"
    assert metadata["simulation_mode"] is False

def test_save_metadata(temp_dir):
    """Test saving metadata to file."""
    metadata = {
        "dataset_source": "test",
        "validation_study_doi": None,
        "stimuli_checksums": {},
        "simulation_mode": False
    }
    output_path = temp_dir / "output.json"
    
    save_metadata(metadata, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        saved = json.load(f)
    
    assert saved == metadata
