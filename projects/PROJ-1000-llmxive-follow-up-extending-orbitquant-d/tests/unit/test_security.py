import os
import json
import tempfile
import hashlib
from pathlib import Path
import pytest

from config import Config
from utils.security import SecurityManager

@pytest.fixture
def temp_project_root(tmp_path):
    """Create a temporary project structure for testing."""
    # Create necessary subdirectories
    (tmp_path / "data").mkdir()
    (tmp_path / "state").mkdir()
    return tmp_path

@pytest.fixture
def security_manager(temp_project_root):
    """Initialize SecurityManager with the temp root."""
    # Mock config to use temp paths
    class MockConfig:
        project_root = temp_project_root
        state_dir = temp_project_root / "state"
        data_dir = temp_project_root / "data"
    
    return SecurityManager(MockConfig())

def test_sanitize_path_basic(security_manager, temp_project_root):
    """Test basic path resolution."""
    safe_path = security_manager.sanitize_path("data/test.txt", temp_project_root)
    expected = temp_project_root / "data" / "test.txt"
    assert safe_path == expected.resolve()

def test_sanitize_path_traversal_attempt(security_manager, temp_project_root):
    """Test that directory traversal is blocked."""
    with pytest.raises(ValueError, match="Path traversal detected"):
        security_manager.sanitize_path("../secrets.txt", temp_project_root)

def test_sanitize_path_absolute_escape(security_manager, temp_project_root):
    """Test that absolute paths outside base are blocked."""
    with pytest.raises(ValueError, match="Path traversal detected"):
        security_manager.sanitize_path("/etc/passwd", temp_project_root)

def test_compute_hash(security_manager, temp_project_root):
    """Test SHA-256 computation."""
    test_file = temp_project_root / "data" / "test.txt"
    content = b"Hello, World!"
    test_file.write_bytes(content)
    
    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = security_manager.compute_hash(test_file)
    
    assert actual_hash == expected_hash

def test_validate_artifact_success(security_manager, temp_project_root):
    """Test successful validation."""
    test_file = temp_project_root / "data" / "valid.txt"
    test_file.write_text("Valid content")
    
    # Register first
    security_manager.register_artifact(test_file)
    
    # Validate
    assert security_manager.validate_artifact(test_file)

def test_validate_artifact_hash_mismatch(security_manager, temp_project_root):
    """Test validation failure on hash mismatch."""
    test_file = temp_project_root / "data" / "tampered.txt"
    test_file.write_text("Original")
    
    # Register
    security_manager.register_artifact(test_file)
    
    # Tamper with file
    test_file.write_text("Tampered")
    
    # Validate should fail
    with pytest.raises(ValueError, match="Integrity check failed"):
        security_manager.validate_artifact(test_file)

def test_validate_artifact_missing_file(security_manager, temp_project_root):
    """Test validation failure when file is missing."""
    test_file = temp_project_root / "data" / "missing.txt"
    
    # Register a fake entry manually to simulate manifest having it
    manifest = security_manager.load_manifest()
    manifest["data/missing.txt"] = "fakehash123"
    security_manager.save_manifest(manifest)
    
    with pytest.raises(FileNotFoundError):
        security_manager.validate_artifact(test_file)

def test_validate_artifact_not_in_manifest(security_manager, temp_project_root):
    """Test validation failure when file is not in manifest."""
    test_file = temp_project_root / "data" / "new.txt"
    test_file.write_text("New content")
    
    # Ensure manifest is empty
    security_manager.save_manifest({})
    
    with pytest.raises(ValueError, match="not found in manifest"):
        security_manager.validate_artifact(test_file)

def test_register_artifact_updates_manifest(security_manager, temp_project_root):
    """Test that registration updates the manifest correctly."""
    test_file = temp_project_root / "data" / "register.txt"
    test_file.write_text("Content")
    
    security_manager.register_artifact(test_file)
    
    manifest = security_manager.load_manifest()
    assert "data/register.txt" in manifest
    assert len(manifest["data/register.txt"]) == 64  # SHA-256 hex length

def test_validate_all_artifacts(security_manager, temp_project_root):
    """Test validation of all artifacts."""
    # Create and register two files
    f1 = temp_project_root / "data" / "file1.txt"
    f2 = temp_project_root / "data" / "file2.txt"
    f1.write_text("1")
    f2.write_text("2")
    
    security_manager.register_artifact(f1)
    security_manager.register_artifact(f2)
    
    # Tamper one
    f2.write_text("Tampered")
    
    results = security_manager.validate_all_artifacts()
    
    assert len(results) == 2
    assert results[0] == ("data/file1.txt", True)
    assert results[1] == ("data/file2.txt", False)

def test_sanitize_path_with_symlinks(security_manager, temp_project_root):
    """Test path sanitization with symlinks (if supported)."""
    # Create a real file
    real_file = temp_project_root / "data" / "real.txt"
    real_file.write_text("Real")
    
    # Create a symlink inside the base
    link_file = temp_project_root / "data" / "link.txt"
    try:
        link_file.symlink_to(real_file)
        
        # Should resolve to the real file, which is still inside base
        safe_path = security_manager.sanitize_path("data/link.txt", temp_project_root)
        assert safe_path == real_file.resolve()
    except (OSError, NotImplementedError):
        # Symlinks not supported on this system (e.g., Windows without admin)
        pytest.skip("Symlinks not supported on this system")

def test_sanitize_path_symlink_escape(security_manager, temp_project_root):
    """Test that symlinks pointing outside base are blocked."""
    # Create a file outside base
    outside_file = temp_project_root.parent / "outside.txt"
    outside_file.write_text("Outside")
    
    # Create a symlink inside base pointing outside
    link_file = temp_project_root / "data" / "escape_link.txt"
    try:
        link_file.symlink_to(outside_file)
        
        with pytest.raises(ValueError, match="Path traversal detected"):
            security_manager.sanitize_path("data/escape_link.txt", temp_project_root)
    except (OSError, NotImplementedError):
        pytest.skip("Symlinks not supported on this system")
