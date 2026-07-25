"""
Tests for the data directory setup script.
"""

import os
import pytest
from pathlib import Path
import tempfile
import shutil

from setup_data_directories import (
    create_directories,
    compute_file_checksum,
    record_checksums,
    save_checksums,
    load_checksums,
    verify_integrity
)


@pytest.fixture
def temp_project_root():
    """Create a temporary directory to simulate project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup after test
    shutil.rmtree(temp_dir)


def test_create_directories(temp_project_root):
    """Test that create_directories creates the expected structure."""
    directories = create_directories(temp_project_root)

    # Check root data directory exists
    assert directories['root'].exists()
    assert directories['root'].is_dir()

    # Check all subdirectories exist
    expected_subdirs = ['raw', 'processed', 'models', 'simulation', 'generated', 'metrics', 'analysis']
    for subdir in expected_subdirs:
        assert directories[subdir].exists()
        assert directories[subdir].is_dir()

def test_create_directories_idempotent(temp_project_root):
    """Test that calling create_directories multiple times is safe."""
    # First call
    dirs1 = create_directories(temp_project_root)
    # Second call
    dirs2 = create_directories(temp_project_root)

    # Paths should be identical
    assert dirs1['root'] == dirs2['root']
    assert dirs1['raw'] == dirs2['raw']

def test_record_checksums(temp_project_root):
    """Test that record_checksums returns valid records for directories."""
    directories = create_directories(temp_project_root)
    checksums = record_checksums(directories)

    assert isinstance(checksums, list)
    assert len(checksums) > 0

    for record in checksums:
        assert 'path' in record
        assert 'type' in record
        assert record['type'] == 'directory'

def test_save_and_load_checksums(temp_project_root):
    """Test saving and loading checksums to/from JSON."""
    directories = create_directories(temp_project_root)
    checksums = record_checksums(directories)

    output_path = temp_project_root / 'state' / 'test_checksums.json'
    save_checksums(checksums, output_path)

    assert output_path.exists()

    loaded_checksums = load_checksums(output_path)

    assert len(loaded_checksums) == len(checksums)
    assert loaded_checksums[0]['path'] == checksums[0]['path']

def test_verify_integrity(temp_project_root):
    """Test that verify_integrity correctly validates directory structure."""
    directories = create_directories(temp_project_root)
    checksums = record_checksums(directories)

    # Should pass when directories exist
    assert verify_integrity(directories, checksums) is True

def test_compute_file_checksum(temp_project_root):
    """Test file checksum computation."""
    test_file = temp_project_root / 'test_file.txt'
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)

    checksum1 = compute_file_checksum(test_file)
    checksum2 = compute_file_checksum(test_file)

    # Same content should produce same checksum
    assert checksum1 == checksum2
    assert len(checksum1) == 64  # SHA-256 hex digest length

    # Modify file and check checksum changes
    test_file.write_bytes(b"Different content")
    checksum3 = compute_file_checksum(test_file)
    assert checksum3 != checksum1