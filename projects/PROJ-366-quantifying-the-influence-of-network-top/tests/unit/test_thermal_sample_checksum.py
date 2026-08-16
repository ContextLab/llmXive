"""
Unit tests for thermal sample checksum generation and verification.

Tests cover:
- Checksum calculation for files
- Finding thermal sample files
- Generating checksums for multiple files
- Saving and loading checksum manifests
- Verifying checksums against manifest
- Error handling for missing files
"""

import json
import os
import pickle
import tempfile
from pathlib import Path
import pytest

from simulation.thermal_sample_checksum import (
    calculate_file_checksum,
    find_thermal_sample_files,
    generate_checksums_for_thermal_samples,
    save_checksum_manifest,
    load_checksum_manifest,
    verify_checksums_against_manifest,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_thermal_data(temp_dir):
    """Create sample thermal sample files."""
    # Create a sample thermal sample object
    sample_data = {
        "graph_id": "test_sample_001",
        "conductivity": 1.23,
        "converged": True,
        "metadata": {
            "atoms": 100,
            "temperature": 300.0,
            "simulation_time": 1000.0
        }
    }

    # Save as pickle
    pkl_path = temp_dir / "sample_001.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(sample_data, f)

    # Save as JSON
    json_path = temp_dir / "sample_002.json"
    with open(json_path, "w") as f:
        json.dump(sample_data, f)

    return temp_dir


def test_calculate_file_checksum(temp_dir):
    """Test checksum calculation for a file."""
    test_file = temp_dir / "test.txt"
    test_content = b"Hello, World!"
    test_file.write_bytes(test_content)

    checksum = calculate_file_checksum(test_file)

    # Verify it's a valid SHA-256 hash
    assert len(checksum) == 64  # SHA-256 produces 64 hex characters
    assert all(c in "0123456789abcdef" for c in checksum)

    # Verify same content produces same checksum
    checksum2 = calculate_file_checksum(test_file)
    assert checksum == checksum2

def test_calculate_file_checksum_nonexistent_file():
    """Test that checksum calculation fails for nonexistent file."""
    with pytest.raises(FileNotFoundError):
        calculate_file_checksum(Path("/nonexistent/file.txt"))

def test_find_thermal_sample_files(temp_dir, sample_thermal_data):
    """Test finding thermal sample files in a directory."""
    files = find_thermal_sample_files(temp_dir)

    assert len(files) >= 2  # At least the pickle and JSON files

    # Check that expected files are found
    file_names = [f.name for f in files]
    assert "sample_001.pkl" in file_names
    assert "sample_002.json" in file_names

def test_find_thermal_sample_files_empty_directory(temp_dir):
    """Test finding files in an empty directory."""
    files = find_thermal_sample_files(temp_dir)
    assert len(files) == 0

def test_find_thermal_sample_files_nonexistent_directory():
    """Test finding files in a nonexistent directory."""
    files = find_thermal_sample_files(Path("/nonexistent/dir"))
    assert len(files) == 0

def test_generate_checksums_for_thermal_samples(temp_dir, sample_thermal_data):
    """Test generating checksums for thermal sample files."""
    output_path = temp_dir / "checksums.json"

    checksums = generate_checksums_for_thermal_samples(temp_dir, output_path)

    assert len(checksums) >= 2
    assert "sample_001.pkl" in checksums
    assert "sample_002.json" in checksums

    # Verify checksums are valid SHA-256 hashes
    for checksum in checksums.values():
        assert len(checksum) == 64
        assert all(c in "0123456789abcdef" for c in checksum)

    # Verify manifest was saved
    assert output_path.exists()

    with open(output_path, "r") as f:
        manifest = json.load(f)

    assert "checksums" in manifest
    assert manifest["algorithm"] == "sha256"

def test_generate_checksums_no_files(temp_dir):
    """Test generating checksums when no files exist."""
    output_path = temp_dir / "checksums.json"
    checksums = generate_checksums_for_thermal_samples(temp_dir, output_path)
    assert len(checksums) == 0

def test_save_and_load_checksum_manifest(temp_dir):
    """Test saving and loading checksum manifests."""
    test_checksums = {
        "file1.pkl": "abc123...",
        "file2.json": "def456..."
    }

    output_path = temp_dir / "test_manifest.json"
    save_checksum_manifest(test_checksums, output_path)

    assert output_path.exists()

    loaded_checksums = load_checksum_manifest(output_path)
    assert loaded_checksums == test_checksums

def test_load_nonexistent_manifest():
    """Test loading a nonexistent manifest."""
    with pytest.raises(FileNotFoundError):
        load_checksum_manifest(Path("/nonexistent/manifest.json"))

def test_verify_checksums_against_manifest(temp_dir, sample_thermal_data):
    """Test verifying checksums against a manifest."""
    # Generate checksums first
    output_path = temp_dir / "checksums.json"
    generate_checksums_for_thermal_samples(temp_dir, output_path)

    # Verify checksums
    results = verify_checksums_against_manifest(temp_dir, output_path)

    assert len(results) >= 2
    assert all(results.values())  # All should be valid

def test_verify_checksums_modified_file(temp_dir, sample_thermal_data):
    """Test verification fails when a file is modified."""
    # Generate checksums
    output_path = temp_dir / "checksums.json"
    generate_checksums_for_thermal_samples(temp_dir, output_path)

    # Modify a file
    pkl_path = temp_dir / "sample_001.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump({"modified": True}, f)

    # Verify checksums - should fail for the modified file
    results = verify_checksums_against_manifest(temp_dir, output_path)

    assert "sample_001.pkl" in results
    assert results["sample_001.pkl"] is False
    assert results["sample_002.json"] is True  # Unchanged file should pass

def test_verify_checksums_missing_file(temp_dir, sample_thermal_data):
    """Test verification handles missing files gracefully."""
    # Generate checksums
    output_path = temp_dir / "checksums.json"
    generate_checksums_for_thermal_samples(temp_dir, output_path)

    # Delete a file
    (temp_dir / "sample_001.pkl").unlink()

    # Verify checksums - should report missing file as invalid
    results = verify_checksums_against_manifest(temp_dir, output_path)

    assert "sample_001.pkl" in results
    assert results["sample_001.pkl"] is False
    assert results["sample_002.json"] is True

def test_verify_nonexistent_manifest(temp_dir, sample_thermal_data):
    """Test verification with nonexistent manifest."""
    results = verify_checksums_against_manifest(
        temp_dir,
        Path("/nonexistent/manifest.json")
    )
    assert len(results) == 0
