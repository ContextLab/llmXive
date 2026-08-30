"""
Unit tests for the hash_artifacts module.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
import pytest
import yaml

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from hash_artifacts import calculate_file_hash, hash_directory, update_artifact_checksum, save_manifest


@pytest.fixture
def temp_file():
    """Create a temporary file with known content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("test content for hashing")
        temp_path = f.name
    yield Path(temp_path)
    os.unlink(temp_path)


@pytest.fixture
def temp_dir():
    """Create a temporary directory with files."""
    temp_path = tempfile.mkdtemp()
    # Create some files
    (Path(temp_path) / "file1.txt").write_text("content 1")
    (Path(temp_path) / "file2.txt").write_text("content 2")
    (Path(temp_path) / "subdir").mkdir()
    (Path(temp_path) / "subdir" / "file3.txt").write_text("content 3")
    yield Path(temp_path)
    import shutil
    shutil.rmtree(temp_path)


def test_calculate_file_hash(temp_file):
    """Test file hash calculation."""
    hash1 = calculate_file_hash(temp_file)
    hash2 = calculate_file_hash(temp_file)
    
    # Same file should produce same hash
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length
    
    # Verify it's actually a hex string
    int(hash1, 16)  # Should not raise


def test_calculate_file_hash_missing_file():
    """Test that missing file raises error."""
    with pytest.raises(FileNotFoundError):
        calculate_file_hash(Path("/nonexistent/file.txt"))


def test_hash_directory(temp_dir):
    """Test directory hashing."""
    hashes = hash_directory(temp_dir)
    
    # Should find 3 files
    assert len(hashes) == 3
    
    # Check specific files exist
    assert "file1.txt" in hashes
    assert "file2.txt" in hashes
    assert "subdir/file3.txt" in hashes
    
    # All values should be valid hex hashes
    for h in hashes.values():
        assert len(h) == 64
        int(h, 16)  # Should not raise


def test_hash_directory_missing():
    """Test hashing non-existent directory."""
    with pytest.raises(FileNotFoundError):
        hash_directory(Path("/nonexistent/dir"))


def test_update_artifact_checksum_integration():
    """Test updating artifact checksum in state file."""
    # This test requires the state file to exist
    state_path = Path(__file__).parent.parent.parent / "state" / "projects" / "PROJ-386-predicting-the-impact-of-processing-temp.yaml"
    
    if not state_path.exists():
        pytest.skip("State file not found, skipping integration test")
        
    # Create a test artifact file
    test_artifact_dir = Path(__file__).parent.parent.parent / "data" / "artifacts"
    test_artifact_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_artifact_dir / "test_checksum.txt"
    test_file.write_text("test checksum content")
    
    try:
        # Update the checksum for a dummy artifact (we'll use collinearity_report as it exists in schema)
        # Note: This modifies the actual state file, so we clean up after
        success = update_artifact_checksum("collinearity_report", "data/artifacts/test_checksum.txt")
        
        # Load state to verify update
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f)
            
        # Verify checksum was updated
        assert state["artifact_registry"]["collinearity_report"]["checksum"] is not None
        assert len(state["artifact_registry"]["collinearity_report"]["checksum"]) == 64
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


def test_save_manifest():
    """Test manifest generation."""
    # Create test artifact
    test_artifact_dir = Path(__file__).parent.parent.parent / "data" / "artifacts"
    test_artifact_dir.mkdir(parents=True, exist_ok=True)
    test_file = test_artifact_dir / "manifest_test.txt"
    test_file.write_text("manifest test content")
    
    try:
        # Update state to include this file
        success = update_artifact_checksum("collinearity_report", "data/artifacts/manifest_test.txt")
        
        # Generate manifest
        manifest_path = test_artifact_dir / "test_manifest.json"
        save_manifest(manifest_path)
        
        # Verify manifest exists and is valid JSON
        assert manifest_path.exists()
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            
        assert "artifacts" in manifest
        assert "collinearity_report" in manifest["artifacts"]
        assert manifest["artifacts"]["collinearity_report"]["checksum"] is not None
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()
        manifest_path = test_artifact_dir / "test_manifest.json"
        if manifest_path.exists():
            manifest_path.unlink()