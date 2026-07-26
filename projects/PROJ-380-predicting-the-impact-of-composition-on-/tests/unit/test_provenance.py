import os
import tempfile
from pathlib import Path
import pytest
import yaml
import hashlib

# Add the code directory to the path to allow imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.provenance import (
    compute_file_checksum,
    record_artifact,
    verify_artifact,
    list_artifacts,
    get_provenance_state_file,
    load_existing_state,
    save_state,
    ensure_state_directory
)
from utils.config import get_paths


@pytest.fixture
def temp_test_file(tmp_path):
    """Create a temporary file with known content for testing."""
    test_file = tmp_path / "test_data.csv"
    content = "col1,col2\n1,2\n3,4\n"
    test_file.write_text(content)
    return test_file


@pytest.fixture
def temp_project_root(tmp_path):
    """Set up a temporary project structure for testing."""
    # Create necessary directories
    (tmp_path / "state" / "projects").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data").mkdir(exist_ok=True)
    return tmp_path


def test_compute_file_checksum(tmp_path):
    """Test that checksum is computed correctly."""
    test_file = tmp_path / "checksum_test.txt"
    content = "Hello, World!"
    test_file.write_text(content)
    
    checksum = compute_file_checksum(test_file)
    
    # Verify against Python's hashlib directly
    expected = hashlib.sha256(content.encode()).hexdigest()
    assert checksum == expected


def test_compute_file_checksum_empty_file(tmp_path):
    """Test that empty file raises ValueError."""
    test_file = tmp_path / "empty.txt"
    test_file.touch()
    
    with pytest.raises(ValueError):
        compute_file_checksum(test_file)


def test_compute_file_checksum_nonexistent(tmp_path):
    """Test that nonexistent file raises FileNotFoundError."""
    test_file = tmp_path / "nonexistent.txt"
    
    with pytest.raises(FileNotFoundError):
        compute_file_checksum(test_file)


def test_record_artifact(tmp_path, temp_test_file):
    """Test that artifact is recorded with correct checksum."""
    # Mock the project root to use our temp directory
    original_get_paths = get_paths
    
    def mock_get_paths():
        return {
            "project_root": tmp_path,
            "data_dir": tmp_path / "data",
            "code_dir": tmp_path / "code",
            "tests_dir": tmp_path / "tests"
        }
    
    # Patch get_paths
    import utils.provenance
    utils.provenance.get_paths = mock_get_paths
    
    try:
        # Record the artifact
        record_artifact(
            temp_test_file,
            description="Test artifact for provenance",
            artifact_type="test_data",
            generated_by="test_provenance.py"
        )
        
        # Verify the state file was created
        state_file = get_provenance_state_file()
        assert state_file.exists()
        
        # Load and verify content
        state = load_existing_state(state_file)
        assert len(state["artifacts"]) == 1
        
        entry = state["artifacts"][0]
        assert entry["path"] == str(temp_test_file.resolve())
        assert entry["description"] == "Test artifact for provenance"
        assert entry["type"] == "test_data"
        assert "checksum" in entry
        assert entry["algorithm"] == "sha256"
    finally:
        # Restore original function
        utils.provenance.get_paths = original_get_paths


def test_verify_artifact_success(tmp_path, temp_test_file):
    """Test that verification passes for unchanged file."""
    original_get_paths = get_paths
    
    def mock_get_paths():
        return {
            "project_root": tmp_path,
            "data_dir": tmp_path / "data",
            "code_dir": tmp_path / "code",
            "tests_dir": tmp_path / "tests"
        }
    
    import utils.provenance
    utils.provenance.get_paths = mock_get_paths
    
    try:
        # Record the artifact
        record_artifact(temp_test_file, "Test artifact")
        
        # Verify should return True
        assert verify_artifact(temp_test_file) is True
    finally:
        utils.provenance.get_paths = original_get_paths


def test_verify_artifact_failure(tmp_path, temp_test_file):
    """Test that verification fails for modified file."""
    original_get_paths = get_paths
    
    def mock_get_paths():
        return {
            "project_root": tmp_path,
            "data_dir": tmp_path / "data",
            "code_dir": tmp_path / "code",
            "tests_dir": tmp_path / "tests"
        }
    
    import utils.provenance
    utils.provenance.get_paths = mock_get_paths
    
    try:
        # Record the artifact
        record_artifact(temp_test_file, "Test artifact")
        
        # Modify the file
        temp_test_file.write_text("Modified content")
        
        # Verify should return False
        assert verify_artifact(temp_test_file) is False
    finally:
        utils.provenance.get_paths = original_get_paths


def test_list_artifacts(tmp_path, temp_test_file):
    """Test listing artifacts."""
    original_get_paths = get_paths
    
    def mock_get_paths():
        return {
            "project_root": tmp_path,
            "data_dir": tmp_path / "data",
            "code_dir": tmp_path / "code",
            "tests_dir": tmp_path / "tests"
        }
    
    import utils.provenance
    utils.provenance.get_paths = mock_get_paths
    
    try:
        # Record an artifact
        record_artifact(temp_test_file, "Test artifact")
        
        # List artifacts
        artifacts = list_artifacts()
        
        assert len(artifacts) == 1
        assert artifacts[0]["description"] == "Test artifact"
    finally:
        utils.provenance.get_paths = original_get_paths


def test_record_multiple_artifacts(tmp_path):
    """Test recording multiple artifacts."""
    original_get_paths = get_paths
    
    def mock_get_paths():
        return {
            "project_root": tmp_path,
            "data_dir": tmp_path / "data",
            "code_dir": tmp_path / "code",
            "tests_dir": tmp_path / "tests"
        }
    
    import utils.provenance
    utils.provenance.get_paths = mock_get_paths
    
    try:
        # Create two test files
        file1 = tmp_path / "data" / "file1.csv"
        file1.parent.mkdir(exist_ok=True)
        file1.write_text("data1")
        
        file2 = tmp_path / "data" / "file2.csv"
        file2.write_text("data2")
        
        # Record both
        record_artifact(file1, "First artifact")
        record_artifact(file2, "Second artifact")
        
        # List should show both
        artifacts = list_artifacts()
        assert len(artifacts) == 2
        
        # Verify both exist in state
        paths = [a["path"] for a in artifacts]
        assert str(file1.resolve()) in paths
        assert str(file2.resolve()) in paths
    finally:
        utils.provenance.get_paths = original_get_paths