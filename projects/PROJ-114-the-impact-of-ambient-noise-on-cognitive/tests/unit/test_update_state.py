"""
Unit tests for update_state.py script.
"""
import os
import tempfile
import yaml
from pathlib import Path
import pytest

# Add the project root to the path to allow imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.update_state import compute_file_hash, scan_artifacts, update_state_file

@pytest.fixture
def temp_project_dir(tmp_path):
    """Create a temporary project structure for testing."""
    # Create directory structure
    dirs = ["code", "data", "tests", "docs", "figures", "contracts", "specs"]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True, exist_ok=True)

    # Create some test files
    (tmp_path / "code" / "test.py").write_text("def hello(): pass")
    (tmp_path / "data" / "test.csv").write_text("a,b\n1,2")
    (tmp_path / "docs" / "readme.md").write_text("# Test")
    
    return tmp_path

def test_compute_file_hash(temp_project_dir):
    """Test SHA-256 hash computation."""
    file_path = temp_project_dir / "code" / "test.py"
    hash1 = compute_file_hash(file_path)
    
    assert len(hash1) == 64  # SHA-256 hex length
    assert all(c in '0123456789abcdef' for c in hash1)
    
    # Verify same file produces same hash
    hash2 = compute_file_hash(file_path)
    assert hash1 == hash2

def test_compute_file_hash_unchanged_content(temp_project_dir):
    """Test that hash changes when content changes."""
    file_path = temp_project_dir / "code" / "test.py"
    hash1 = compute_file_hash(file_path)
    
    file_path.write_text("def hello(): pass\n# new line")
    hash2 = compute_file_hash(file_path)
    
    assert hash1 != hash2

def test_scan_artifacts(temp_project_dir):
    """Test artifact scanning and hashing."""
    artifacts = scan_artifacts(temp_project_dir, ["code", "data", "docs"])
    
    assert len(artifacts) == 3
    
    paths = [a["path"] for a in artifacts]
    assert "code/test.py" in paths
    assert "data/test.csv" in paths
    assert "docs/readme.md" in paths
    
    # Check hash exists
    for artifact in artifacts:
        assert "hash" in artifact
        assert len(artifact["hash"]) == 64

def test_update_state_file(temp_project_dir):
    """Test state file creation and content."""
    state_dir = temp_project_dir / "state" / "projects" / "TEST-001"
    artifacts = [
        {"path": "code/test.py", "hash": "abc123", "size_bytes": 10, "modified": "2023-01-01"}
    ]
    
    update_state_file(state_dir, artifacts, "TEST-001")
    
    state_file = state_dir / "current_stage.yaml"
    assert state_file.exists()
    
    with open(state_file, "r") as f:
        content = yaml.safe_load(f)
    
    assert content["project_id"] == "TEST-001"
    assert content["artifact_count"] == 1
    assert len(content["artifacts"]) == 1
    assert content["artifacts"][0]["path"] == "code/test.py"
    assert "last_updated" in content