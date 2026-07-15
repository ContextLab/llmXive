import os
import subprocess
import yaml
import tempfile
import shutil
from pathlib import Path
import pytest

# We need to run the script in the context of the project
# Since we are in tests/, we assume the project root is one level up
PROJECT_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "hash_artifacts.sh"

@pytest.fixture
def temp_project_structure():
    """Create a temporary project structure for testing."""
    # Create a temp dir
    temp_dir = tempfile.mkdtemp()
    # Copy necessary files structure
    # We simulate the structure by creating dummy files in the temp dir
    # But since we are testing the script, we need the script to exist
    # So we run the script in the actual project root, but we can't easily 
    # change the root without modifying the script or passing args.
    # For this test, we assume the script runs successfully in the actual repo.
    # We will test the output file existence and format.
    
    return PROJECT_ROOT

def test_script_exists():
    assert SCRIPT_PATH.exists(), "hash_artifacts.sh must exist"

def test_script_executable():
    assert os.access(SCRIPT_PATH, os.X_OK), "hash_artifacts.sh must be executable"

def test_manifest_generation(temp_project_structure):
    """Test that running the script generates a valid manifest."""
    # Ensure state directory exists
    state_dir = temp_project_structure / "state"
    state_dir.mkdir(exist_ok=True)
    
    manifest_path = state_dir / "manifest.yaml"
    checksum_path = state_dir / "checksums.txt"
    
    # Remove old files if they exist
    if manifest_path.exists():
        manifest_path.unlink()
    if checksum_path.exists():
        checksum_path.unlink()

    # Run the script
    result = subprocess.run(
        ["bash", str(SCRIPT_PATH)],
        cwd=temp_project_structure,
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Script failed: {result.stderr}"
    
    assert manifest_path.exists(), "Manifest file was not created"
    assert checksum_path.exists(), "Checksums file was not created"

    # Validate YAML structure
    with open(manifest_path, 'r') as f:
        data = yaml.safe_load(f)
    
    assert "version" in data, "Manifest must have a version"
    assert "files" in data, "Manifest must have a files list"
    assert isinstance(data["files"], list), "Files must be a list"

    if len(data["files"]) > 0:
        first_file = data["files"][0]
        assert "path" in first_file, "File entry must have a path"
        assert "sha256" in first_file, "File entry must have a sha256"
        assert len(first_file["sha256"]) == 64, "SHA256 must be 64 chars"

def test_checksums_format(temp_project_structure):
    """Test that checksums file has correct format."""
    checksum_path = temp_project_structure / "state" / "checksums.txt"
    
    if not checksum_path.exists():
        # Run script first
        subprocess.run(["bash", str(SCRIPT_PATH)], cwd=temp_project_structure, check=True)

    with open(checksum_path, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        parts = line.strip().split("  ")
        assert len(parts) == 2, "Checksum line format must be 'hash  path'"
        assert len(parts[0]) == 64, "Hash must be 64 chars"
        assert len(parts[1]) > 0, "Path must not be empty"
