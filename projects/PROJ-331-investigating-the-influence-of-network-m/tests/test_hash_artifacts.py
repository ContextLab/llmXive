"""
Test suite for scripts/hash_artifacts.sh
Verifies that the hash generation script correctly computes checksums
and updates the state manifest.
"""
import os
import subprocess
import tempfile
import shutil
import yaml
import hashlib
from pathlib import Path
import pytest

@pytest.fixture
def temp_project_root():
    """Create a temporary project structure for testing."""
    temp_dir = tempfile.mkdtemp(prefix="hash_test_")
    
    # Create directory structure
    dirs = [
        "code", "tests", "data/raw", "data/processed", 
        "data/logs", "results", "state", "specs"
    ]
    for d in dirs:
        os.makedirs(os.path.join(temp_dir, d), exist_ok=True)
    
    # Create some dummy files
    test_files = {
        "code/config.py": "PROJECT_NAME = 'test'",
        "code/utils.py": "def dummy(): pass",
        "data/processed/test.npy": "dummy binary content",
        "results/report.pdf": "dummy pdf content",
        "tests/test_dummy.py": "def test_dummy(): pass",
    }
    
    for path, content in test_files.items():
        full_path = os.path.join(temp_dir, path)
        with open(full_path, 'w') as f:
            f.write(content)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_script_exists():
    """Verify the hash script exists in the project."""
    script_path = Path("scripts/hash_artifacts.sh")
    assert script_path.exists(), "scripts/hash_artifacts.sh must exist"

def test_script_executable():
    """Verify the script has executable permissions or can be run via bash."""
    script_path = Path("scripts/hash_artifacts.sh")
    if script_path.exists():
        # Try to run with bash to verify syntax
        result = subprocess.run(
            ["bash", "-n", str(script_path)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Script has syntax errors: {result.stderr}"

def test_hash_generation(temp_project_root):
    """Test that the script generates checksums correctly."""
    script_path = Path("scripts/hash_artifacts.sh")
    
    # Run the script in the temp directory
    result = subprocess.run(
        ["bash", str(script_path)],
        cwd=temp_project_root,
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    # Verify checksums file was created
    checksums_file = os.path.join(temp_project_root, "state", "checksums.txt")
    assert os.path.exists(checksums_file), "Checksums file should be created"
    
    # Verify manifest was created
    manifest_file = os.path.join(temp_project_root, "state", "manifest.yaml")
    assert os.path.exists(manifest_file), "Manifest file should be created"
    
    # Verify manifest is valid YAML
    with open(manifest_file, 'r') as f:
        manifest = yaml.safe_load(f)
    
    assert "artifacts" in manifest, "Manifest must contain 'artifacts' key"
    assert manifest["project_id"] == "PROJ-331", "Project ID should match"
    assert "generated_at" in manifest, "Timestamp should be present"

def test_checksum_accuracy(temp_project_root):
    """Verify that computed checksums match actual file hashes."""
    script_path = Path("scripts/hash_artifacts.sh")
    
    # Run the script
    subprocess.run(
        ["bash", str(script_path)],
        cwd=temp_project_root,
        capture_output=True,
        text=True
    )
    
    # Read the manifest
    manifest_file = os.path.join(temp_project_root, "state", "manifest.yaml")
    with open(manifest_file, 'r') as f:
        manifest = yaml.safe_load(f)
    
    # Verify each artifact's checksum
    for artifact in manifest["artifacts"]:
        if artifact["path"] == "(none)":
            continue
            
        file_path = os.path.join(temp_project_root, artifact["path"])
        assert os.path.exists(file_path), f"File {artifact['path']} should exist"
        
        # Compute actual hash
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_hash = sha256_hash.hexdigest()
        
        assert artifact["checksum"] == actual_hash, \
            f"Checksum mismatch for {artifact['path']}: expected {actual_hash}, got {artifact['checksum']}"

def test_empty_directory_handling():
    """Test script behavior when directories are empty."""
    temp_dir = tempfile.mkdtemp(prefix="hash_empty_")
    try:
        # Create only state directory
        os.makedirs(os.path.join(temp_dir, "state"))
        
        script_path = Path("scripts/hash_artifacts.sh")
        result = subprocess.run(
            ["bash", str(script_path)],
            cwd=temp_dir,
            capture_output=True,
            text=True
        )
        
        # Should succeed even with no files
        assert result.returncode == 0
        
        # Verify manifest exists
        manifest_file = os.path.join(temp_dir, "state", "manifest.yaml")
        assert os.path.exists(manifest_file)
        
        with open(manifest_file, 'r') as f:
            manifest = yaml.safe_load(f)
        
        # Should have empty artifacts list
        assert len(manifest["artifacts"]) == 1
        assert manifest["artifacts"][0]["path"] == "(none)"
        
    finally:
        shutil.rmtree(temp_dir)
