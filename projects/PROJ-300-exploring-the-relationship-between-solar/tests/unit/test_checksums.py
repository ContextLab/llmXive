"""
Unit tests for checksum functionality (T042).
Verifies Constitution Principle V implementation.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.checksums import compute_sha256, scan_artifacts, generate_state_file, verify_checksums

@pytest.fixture
def temp_project_dir():
    """Create a temporary project structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create test structure
        (root / "code").mkdir()
        (root / "data").mkdir()
        (root / "data" / "raw").mkdir()
        (root / "data" / "processed").mkdir()
        (root / "tests").mkdir()
        
        # Create test files
        (root / "code" / "test.py").write_text("x = 1\n")
        (root / "data" / "raw" / "test.csv").write_text("a,b\n1,2\n")
        (root / "data" / "processed" / "report.json").write_text('{"key": "value"}')
        (root / "README.md").write_text("# Test Project")
        
        yield root

def test_compute_sha256(temp_project_dir):
    """Test SHA-256 computation on a known file."""
    file_path = temp_project_dir / "code" / "test.py"
    checksum = compute_sha256(file_path)
    
    assert len(checksum) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in checksum)

def test_scan_artifacts(temp_project_dir):
    """Test artifact scanning and checksumming."""
    # Temporarily override PROJECT_ROOT
    import code.checksums as checksums_module
    original_root = checksums_module.PROJECT_ROOT
    checksums_module.PROJECT_ROOT = temp_project_dir
    
    try:
        artifacts = scan_artifacts(temp_project_dir)
        
        assert len(artifacts) >= 4  # At least our test files
        
        paths = [a["path"] for a in artifacts]
        assert "code/test.py" in paths
        assert "data/raw/test.csv" in paths
        assert "data/processed/report.json" in paths
        assert "README.md" in paths
        
        # Verify checksums are present and valid
        for artifact in artifacts:
            assert "checksum" in artifact
            assert len(artifact["checksum"]) == 64
            assert "size_bytes" in artifact
            assert artifact["size_bytes"] > 0
    finally:
        checksums_module.PROJECT_ROOT = original_root

def test_generate_state_file(temp_project_dir):
    """Test state file generation."""
    import code.checksums as checksums_module
    original_root = checksums_module.PROJECT_ROOT
    checksums_module.PROJECT_ROOT = temp_project_dir
    
    try:
        state_path = temp_project_dir / "data" / "processed" / "test_state.json"
        artifacts = scan_artifacts(temp_project_dir)
        generate_state_file(artifacts, state_path)
        
        assert state_path.exists()
        
        with open(state_path, "r") as f:
            state = json.load(f)
        
        assert "generated_at" in state
        assert "artifacts" in state
        assert "project_id" in state
        assert state["project_id"] == "PROJ-300-exploring-the-relationship-between-solar"
        assert len(state["artifacts"]) == len(artifacts)
    finally:
        checksums_module.PROJECT_ROOT = original_root

def test_verify_checksums_success(temp_project_dir):
    """Test successful checksum verification."""
    import code.checksums as checksums_module
    original_root = checksums_module.PROJECT_ROOT
    checksums_module.PROJECT_ROOT = temp_project_dir
    
    try:
        state_path = temp_project_dir / "data" / "processed" / "verify_state.json"
        artifacts = scan_artifacts(temp_project_dir)
        generate_state_file(artifacts, state_path)
        
        assert verify_checksums(state_path) is True
    finally:
        checksums_module.PROJECT_ROOT = original_root

def test_verify_checksums_failure(temp_project_dir):
    """Test checksum verification failure when file is modified."""
    import code.checksums as checksums_module
    original_root = checksums_module.PROJECT_ROOT
    checksums_module.PROJECT_ROOT = temp_project_dir
    
    try:
        state_path = temp_project_dir / "data" / "processed" / "verify_fail_state.json"
        artifacts = scan_artifacts(temp_project_dir)
        generate_state_file(artifacts, state_path)
        
        # Modify a file
        test_file = temp_project_dir / "code" / "test.py"
        test_file.write_text("x = 2\n")  # Changed content
        
        assert verify_checksums(state_path) is False
    finally:
        checksums_module.PROJECT_ROOT = original_root

def test_verify_checksums_missing_file(temp_project_dir):
    """Test checksum verification when a file is missing."""
    import code.checksums as checksums_module
    original_root = checksums_module.PROJECT_ROOT
    checksums_module.PROJECT_ROOT = temp_project_dir
    
    try:
        state_path = temp_project_dir / "data" / "processed" / "missing_state.json"
        artifacts = scan_artifacts(temp_project_dir)
        generate_state_file(artifacts, state_path)
        
        # Delete a file
        test_file = temp_project_dir / "code" / "test.py"
        test_file.unlink()
        
        assert verify_checksums(state_path) is False
    finally:
        checksums_module.PROJECT_ROOT = original_root
