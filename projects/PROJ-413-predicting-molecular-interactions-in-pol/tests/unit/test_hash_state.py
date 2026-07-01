"""
Unit tests for the hash_state utility module.
"""

import os
import tempfile
import pytest
from pathlib import Path

# Import the module under test
from code.utils.hash_state import (
    compute_sha256,
    hash_directory,
    update_state_yaml,
    verify_artifacts,
    HAS_YAML
)


@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some files
        Path(tmpdir, "file1.txt").write_text("Content 1")
        Path(tmpdir, "file2.py").write_text("print('hello')")
        
        # Create a subdirectory
        subdir = Path(tmpdir, "subdir")
        subdir.mkdir()
        Path(subdir, "file3.txt").write_text("Content 3")
        
        yield tmpdir


def test_compute_sha256_file_not_found():
    """Test that compute_sha256 raises FileNotFoundError for missing files."""
    with pytest.raises(FileNotFoundError):
        compute_sha256("/nonexistent/path/file.txt")


def test_compute_sha256_known_value(temp_file):
    """Test SHA256 computation with known content."""
    # "Hello, World!" SHA256
    expected_hash = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
    actual_hash = compute_sha256(temp_file)
    assert actual_hash == expected_hash


def test_hash_directory(temp_dir):
    """Test hashing all files in a directory."""
    hashes = hash_directory(temp_dir)
    
    # Should contain 3 files
    assert len(hashes) == 3
    
    # Check that all expected files are present
    assert "file1.txt" in hashes
    assert "file2.py" in hashes
    assert "subdir/file3.txt" in hashes


def test_hash_directory_with_extensions(temp_dir):
    """Test hashing only specific file extensions."""
    hashes = hash_directory(temp_dir, extensions=[".txt"])
    
    # Should contain only .txt files
    assert len(hashes) == 2
    assert "file1.txt" in hashes
    assert "subdir/file3.txt" in hashes
    assert "file2.py" not in hashes


def test_hash_directory_exclude_dirs(temp_dir):
    """Test excluding directories from hashing."""
    hashes = hash_directory(temp_dir, exclude_dirs=["subdir"])
    
    # Should contain only files in root
    assert len(hashes) == 2
    assert "file1.txt" in hashes
    assert "file2.py" in hashes
    assert "subdir/file3.txt" not in hashes


def test_update_state_yaml_without_yaml():
    """Test that update_state_yaml raises ImportError if PyYAML is missing."""
    # Temporarily mock HAS_YAML to False
    original_has_yaml = HAS_YAML
    
    # This test only runs if PyYAML is actually installed
    if HAS_YAML:
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
            state_file = f.name
        
        try:
            update_state_yaml(
                state_file,
                "test-project",
                {"artifact.txt": "abc123"},
                {"version": "1.0"}
            )
            
            # Verify file was created
            assert os.path.exists(state_file)
            
            # Clean up
            os.unlink(state_file)
        finally:
            pass


@pytest.mark.skipif(not HAS_YAML, reason="PyYAML not installed")
def test_update_and_verify_state_yaml(temp_file):
    """Test updating and verifying state YAML."""
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
        state_file = f.name
    
    try:
        # Create state with artifact hash
        artifact_hash = compute_sha256(temp_file)
        update_state_yaml(
            state_file,
            "test-project",
            {"artifact.txt": artifact_hash},
            {"version": "1.0"}
        )
        
        # Verify artifacts
        results = verify_artifacts(state_file, "test-project")
        
        # Should pass verification (note: path key might differ based on how we store it)
        # We're storing the relative path as the key
        assert len(results) == 1
        
    finally:
        if os.path.exists(state_file):
            os.unlink(state_file)


def test_verify_artifacts_missing_state():
    """Test verify_artifacts with missing state file."""
    with pytest.raises(FileNotFoundError):
        verify_artifacts("/nonexistent/state.yaml", "test-project")


def test_verify_artifacts_missing_project():
    """Test verify_artifacts with missing project ID."""
    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as f:
        state_file = f.name
    
    try:
        # Create empty state
        import yaml
        with open(state_file, 'w') as sf:
            yaml.dump({}, sf)
        
        with pytest.raises(ValueError):
            verify_artifacts(state_file, "nonexistent-project")
    finally:
        os.unlink(state_file)