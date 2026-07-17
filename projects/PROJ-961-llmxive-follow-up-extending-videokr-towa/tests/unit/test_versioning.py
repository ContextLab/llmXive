import json
import os
import tempfile
from pathlib import Path
import pytest

from utils.versioning import compute_sha256, verify_artifact, write_version_manifest, write_project_state_yaml
from utils.config import get_project_root

def test_compute_sha256():
    """Test that SHA-256 computation is deterministic and correct."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    try:
        hash1 = compute_sha256(temp_path)
        hash2 = compute_sha256(temp_path)
        
        # Should be deterministic
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 hex length
        
        # Known hash for "test content"
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        assert hash1 == expected
    finally:
        os.unlink(temp_path)

def test_verify_artifact():
    """Test artifact verification."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("verify me")
        temp_path = f.name
    
    try:
        correct_hash = compute_sha256(temp_path)
        wrong_hash = "0" * 64
        
        assert verify_artifact(temp_path, correct_hash) is True
        assert verify_artifact(temp_path, wrong_hash) is False
    finally:
        os.unlink(temp_path)

def test_write_version_manifest():
    """Test writing a version manifest JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "manifest.json"
        artifacts = {"file1.txt": "hash1", "file2.txt": "hash2"}
        
        write_version_manifest(artifacts, output_path)
        
        assert output_path.exists()
        
        with open(output_path, 'r') as f:
            manifest = json.load(f)
        
        assert manifest["artifacts"] == artifacts
        assert "version" in manifest

def test_write_project_state_yaml():
    """Test writing project state YAML."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "project.yaml"
        project_id = "TEST-001"
        artifacts = {"data.csv": "abc123", "model.pkl": "def456"}
        
        write_project_state_yaml(project_id, artifacts, output_path)
        
        assert output_path.exists()
        
        content = output_path.read_text()
        assert f"project_id: {project_id}" in content
        assert "data.csv: abc123" in content
        assert "model.pkl: def456" in content
        # Check YAML structure
        assert "artifacts:" in content
        assert "    data.csv:" in content