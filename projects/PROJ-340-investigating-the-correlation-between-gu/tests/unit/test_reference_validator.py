import os
import json
import tempfile
import shutil
import yaml
from pathlib import Path
import pytest

from reference_validator import ReferenceValidator, VerificationStatus

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    temp_dir = tempfile.mkdtemp()
    project_root = Path(temp_dir)
    
    # Create necessary subdirectories
    (project_root / "state" / "projects").mkdir(parents=True, exist_ok=True)
    (project_root / "data").mkdir(parents=True, exist_ok=True)
    
    yield project_root
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_calculate_sha256(temp_project_root):
    """Test SHA256 calculation."""
    validator = ReferenceValidator(str(temp_project_root))
    
    # Create a test file
    test_file = temp_project_root / "data" / "test.txt"
    test_content = "Hello, World!"
    test_file.write_text(test_content)
    
    checksum = validator.calculate_sha256(str(test_file))
    
    assert checksum.startswith("sha256:")
    assert len(checksum) == 71  # "sha256:" + 64 hex chars

def test_record_artifact_checksum(temp_project_root):
    """Test recording an artifact checksum."""
    validator = ReferenceValidator(str(temp_project_root))
    
    # Create a test file
    test_file = temp_project_root / "data" / "test.txt"
    test_content = "Test content for checksum"
    test_file.write_text(test_content)
    
    # Record checksum
    checksum = validator.record_artifact_checksum(str(test_file))
    
    # Verify checksum was recorded in state
    state_file = temp_project_root / "state" / "projects" / "PROJ-340-investigating-the-correlation-between-gu.yaml"
    assert state_file.exists()
    
    with open(state_file, 'r') as f:
        state = yaml.safe_load(f)
    
    assert "artifact_hashes" in state
    assert str(test_file) in state["artifact_hashes"]
    assert state["artifact_hashes"][str(test_file)] == checksum

def test_record_nonexistent_file(temp_project_root):
    """Test recording checksum for a nonexistent file raises error."""
    validator = ReferenceValidator(str(temp_project_root))
    
    with pytest.raises(FileNotFoundError):
        validator.record_artifact_checksum("/nonexistent/file.txt")

def test_verify_artifact_success(temp_project_root):
    """Test successful artifact verification."""
    validator = ReferenceValidator(str(temp_project_root))
    
    # Create and record a file
    test_file = temp_project_root / "data" / "test.txt"
    test_content = "Verification test"
    test_file.write_text(test_content)
    
    checksum = validator.record_artifact_checksum(str(test_file))
    
    # Verify
    result = validator.verify_artifact(str(test_file), checksum)
    
    assert result.status == VerificationStatus.SUCCESS
    assert "Artifact verified" in result.message

def test_verify_artifact_failure(temp_project_root):
    """Test artifact verification failure due to checksum mismatch."""
    validator = ReferenceValidator(str(temp_project_root))
    
    # Create and record a file
    test_file = temp_project_root / "data" / "test.txt"
    test_content = "Verification test"
    test_file.write_text(test_content)
    
    checksum = validator.record_artifact_checksum(str(test_file))
    
    # Verify with wrong checksum
    wrong_checksum = checksum.replace("a", "b")
    result = validator.verify_artifact(str(test_file), wrong_checksum)
    
    assert result.status == VerificationStatus.FAILED
    assert "Checksum mismatch" in result.message

def test_validate_pipeline_state(temp_project_root):
    """Test pipeline state validation."""
    validator = ReferenceValidator(str(temp_project_root))
    
    # Initially, state file might not exist or be empty
    result = validator.validate_pipeline_state()
    
    # Should be WARNING or SUCCESS depending on initial state
    assert result.status in [VerificationStatus.WARNING, VerificationStatus.SUCCESS]

def test_state_file_creation(temp_project_root):
    """Test that state file is created if it doesn't exist."""
    validator = ReferenceValidator(str(temp_project_root))
    
    state_file = temp_project_root / "state" / "projects" / "PROJ-340-investigating-the-correlation-between-gu.yaml"
    
    # Ensure it doesn't exist
    if state_file.exists():
        state_file.unlink()
    
    # Create a test file and record it
    test_file = temp_project_root / "data" / "test.txt"
    test_file.write_text("Test")
    
    validator.record_artifact_checksum(str(test_file))
    
    # State file should now exist
    assert state_file.exists()