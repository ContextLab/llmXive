"""
Tests for T021: Checksum Manager functionality.

Tests that:
1. Checksums are correctly calculated for files
2. Project state YAML is updated with artifact hashes
3. Local checksums.txt is updated as secondary
4. Integrity verification works correctly
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml
import shutil
from datetime import datetime

# Import the module under test
from checksum_manager import (
    calculate_file_sha256,
    update_artifact_hash,
    verify_artifact_integrity,
    load_project_state,
    list_artifacts
)
from config import get_config, reset_config, load_config
from logging_config import setup_logging

@pytest.fixture
def temp_test_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    # Setup a temporary project structure
    test_dir = tmp_path / "test_project"
    test_dir.mkdir()
    
    data_raw = test_dir / "data" / "raw"
    data_raw.mkdir(parents=True)
    
    state_dir = test_dir / "state" / "projects"
    state_dir.mkdir(parents=True)
    
    # Create a test file
    test_file = data_raw / "test_species.fasta"
    test_file.write_text(">species1\nATCGATCGATCG\n>species2\nGCTAGCTAGCTA\n")
    
    # Create a minimal config
    config_path = test_dir / "config.yaml"
    config_content = {
        "project_id": "PROJ-408-test",
        "data_raw_dir": str(data_raw),
        "state_file_path": str(state_dir / "PROJ-408-test.yaml")
    }
    with open(config_path, 'w') as f:
        yaml.dump(config_content, f)
    
    return {
        "base_dir": test_dir,
        "data_raw": data_raw,
        "state_dir": state_dir,
        "test_file": test_file,
        "config_path": config_path
    }

@pytest.fixture
def setup_config(temp_test_dir):
    """Setup config for the test."""
    reset_config()
    config = load_config(temp_test_dir["config_path"])
    return config

def test_calculate_file_sha256(setup_config, temp_test_dir):
    """Test that SHA-256 is correctly calculated for a file."""
    test_file = temp_test_dir["test_file"]
    checksum = calculate_file_sha256(test_file)
    
    # Verify it's a valid SHA-256 hex string (64 chars)
    assert len(checksum) == 64
    assert all(c in '0123456789abcdef' for c in checksum)
    
    # Verify consistency (same file = same checksum)
    checksum2 = calculate_file_sha256(test_file)
    assert checksum == checksum2

def test_update_artifact_hash_updates_state(setup_config, temp_test_dir):
    """Test that update_artifact_hash correctly updates the state YAML."""
    test_file = temp_test_dir["test_file"]
    artifact_name = "raw/test_species.fasta"
    
    # Update the hash
    checksum = update_artifact_hash(artifact_name, test_file)
    
    # Load state and verify
    state_path = temp_test_dir["state_dir"] / "PROJ-408-test.yaml"
    state = load_project_state(state_path)
    
    assert "artifact_hashes" in state
    assert artifact_name in state["artifact_hashes"]
    
    entry = state["artifact_hashes"][artifact_name]
    assert entry["checksum"] == checksum
    assert entry["path"] == str(test_file)
    assert entry["algorithm"] == "sha256"
    assert "size_bytes" in entry
    assert "last_updated" in state

def test_update_artifact_hash_creates_checksums_txt(setup_config, temp_test_dir):
    """Test that update_artifact_hash creates/updates checksums.txt."""
    test_file = temp_test_dir["test_file"]
    artifact_name = "raw/test_species.fasta"
    
    update_artifact_hash(artifact_name, test_file)
    
    checksums_file = temp_test_dir["data_raw"] / "checksums.txt"
    assert checksums_file.exists()
    
    content = checksums_file.read_text()
    assert artifact_name in content
    assert len(content.split('|')) > 1  # Should have checksum after pipe

def test_verify_artifact_integrity_pass(setup_config, temp_test_dir):
    """Test that verify_artifact_integrity returns True for valid files."""
    test_file = temp_test_dir["test_file"]
    artifact_name = "raw/test_species.fasta"
    
    update_artifact_hash(artifact_name, test_file)
    
    result = verify_artifact_integrity(artifact_name)
    assert result is True

def test_verify_artifact_integrity_fail_modified(setup_config, temp_test_dir):
    """Test that verify_artifact_integrity returns False for modified files."""
    test_file = temp_test_dir["test_file"]
    artifact_name = "raw/test_species.fasta"
    
    # Register original file
    update_artifact_hash(artifact_name, test_file)
    
    # Modify the file
    test_file.write_text(">modified\nAAAA\n")
    
    # Verify should fail
    result = verify_artifact_integrity(artifact_name)
    assert result is False

def test_verify_artifact_integrity_missing_file(setup_config, temp_test_dir):
    """Test that verify_artifact_integrity handles missing files."""
    test_file = temp_test_dir["test_file"]
    artifact_name = "raw/test_species.fasta"
    
    update_artifact_hash(artifact_name, test_file)
    
    # Delete the file
    test_file.unlink()
    
    result = verify_artifact_integrity(artifact_name)
    assert result is False

def test_list_artifacts(setup_config, temp_test_dir):
    """Test that list_artifacts returns all registered artifacts."""
    test_file = temp_test_dir["test_file"]
    
    # Register multiple artifacts
    update_artifact_hash("raw/species1.fasta", test_file)
    update_artifact_hash("raw/species2.fasta", test_file)
    
    artifacts = list_artifacts()
    
    assert len(artifacts) == 2
    assert "raw/species1.fasta" in artifacts
    assert "raw/species2.fasta" in artifacts

def test_large_file_checksum(setup_config, temp_test_dir):
    """Test checksum calculation on a larger file (streaming)."""
    large_file = temp_test_dir["data_raw"] / "large_file.fasta"
    
    # Create a ~1MB file
    with open(large_file, 'w') as f:
        for i in range(100000):
            f.write(f">sequence_{i}\n")
            f.write("ATCG" * 250 + "\n")
    
    checksum = calculate_file_sha256(large_file)
    assert len(checksum) == 64
    
    # Verify consistency
    checksum2 = calculate_file_sha256(large_file)
    assert checksum == checksum2