"""
Unit tests for manifest verification functionality.
"""
import os
import sys
import tempfile
import json
import hashlib
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.utils.manifest_verifier import (
    verify_artifact_integrity,
    verify_manifest_integrity,
    generate_verification_report,
    save_verification_report
)
from src.utils.manifest_manager import compute_file_hash, MANIFEST_PATH


@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        
        # Create necessary directories
        (root / "data").mkdir()
        (root / "artifacts").mkdir()
        (root / "state").mkdir()
        
        yield root

@pytest.fixture
def sample_manifest(temp_project_root):
    """Create a sample manifest file."""
    manifest = {
        "version": "1.0",
        "artifacts": {
            "data/raw/dataset.csv": {
                "hash": "abc123",
                "type": "dataset"
            },
            "artifacts/model.pkl": {
                "hash": "def456",
                "type": "model"
            }
        }
    }
    
    manifest_path = temp_project_root / MANIFEST_PATH
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    
    return manifest

@pytest.fixture
def valid_artifact(temp_project_root):
    """Create a valid artifact file."""
    artifact_path = temp_project_root / "data" / "test.txt"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    content = "test content"
    artifact_path.write_text(content)
    return artifact_path, compute_file_hash(str(artifact_path))

def test_verify_artifact_integrity_success(valid_artifact, temp_project_root):
    """Test successful artifact verification."""
    artifact_path, expected_hash = valid_artifact
    relative_path = str(artifact_path.relative_to(temp_project_root))
    
    success, message = verify_artifact_integrity(relative_path, expected_hash, temp_project_root)
    
    assert success is True
    assert "Verified" in message

def test_verify_artifact_integrity_missing_file(temp_project_root):
    """Test verification fails when file is missing."""
    success, message = verify_artifact_integrity("nonexistent.txt", "abc123", temp_project_root)
    
    assert success is False
    assert "missing" in message

def test_verify_artifact_integrity_hash_mismatch(valid_artifact, temp_project_root):
    """Test verification fails when hash doesn't match."""
    artifact_path, _ = valid_artifact
    relative_path = str(artifact_path.relative_to(temp_project_root))
    
    success, message = verify_artifact_integrity(relative_path, "wrong_hash", temp_project_root)
    
    assert success is False
    assert "mismatch" in message

def test_verify_manifest_integrity_success(temp_project_root):
    """Test full manifest verification with all valid artifacts."""
    # Create manifest
    manifest = {
        "version": "1.0",
        "artifacts": {}
    }
    
    # Create a valid artifact and add to manifest
    artifact_path = temp_project_root / "data" / "valid.txt"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text("valid content")
    file_hash = compute_file_hash(str(artifact_path))
    
    manifest["artifacts"]["data/valid.txt"] = {
        "hash": file_hash,
        "type": "test"
    }
    
    # Write manifest
    manifest_path = temp_project_root / MANIFEST_PATH
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    
    success, passed, failed = verify_manifest_integrity(temp_project_root)
    
    assert success is True
    assert len(passed) == 1
    assert len(failed) == 0

def test_verify_manifest_integrity_missing_artifact(temp_project_root):
    """Test manifest verification when an artifact is missing."""
    manifest = {
        "version": "1.0",
        "artifacts": {
            "data/missing.txt": {
                "hash": "abc123",
                "type": "test"
            }
        }
    }
    
    manifest_path = temp_project_root / MANIFEST_PATH
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f)
    
    success, passed, failed = verify_manifest_integrity(temp_project_root)
    
    assert success is False
    assert len(failed) == 1
    assert "missing" in failed[0]

def test_verify_manifest_integrity_missing_manifest(temp_project_root):
    """Test when manifest file doesn't exist."""
    success, passed, failed = verify_manifest_integrity(temp_project_root)
    
    assert success is False
    assert len(failed) == 1
    assert "Manifest missing" in failed[0]

def test_generate_verification_report(temp_project_root):
    """Test report generation."""
    success = True
    passed = ["Verified: data/test.txt"]
    failed = []
    
    report = generate_verification_report(temp_project_root, success, passed, failed)
    
    assert report["verification_status"] == "PASSED"
    assert report["total_artifacts"] == 1
    assert report["passed_count"] == 1
    assert report["failed_count"] == 0

def test_save_verification_report(temp_project_root):
    """Test saving verification report."""
    report = {
        "verification_status": "PASSED",
        "total_artifacts": 0,
        "passed_count": 0,
        "failed_count": 0,
        "passed_artifacts": [],
        "failed_artifacts": [],
        "manifest_path": "state/manifest.json"
    }
    
    report_path = save_verification_report(report, temp_project_root)
    
    assert os.path.exists(report_path)
    assert "manifest_verification_report.json" in report_path
    
    with open(report_path, 'r') as f:
        saved_report = json.load(f)
    
    assert saved_report["verification_status"] == "PASSED"
